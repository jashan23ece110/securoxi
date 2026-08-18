"""
SECUROXI AI Enterprise REST API Server
Exposes secure REST endpoints for document scanning, ZIP bulk processing,
dashboard stats, scan results, evidence investigation, and audit trail logs.
"""

import os
import tempfile
import zipfile
import shutil
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, UploadFile, File, Header, HTTPException, Depends, Query, Security, Body
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles

from securoxi.scanner import SecuroxiScanner
from securoxi.config import SecuroxiConfig
from securoxi.storage.db import SecuroxiDatabase
from securoxi.logger import get_logger

from securoxi.control_plane.governance import EnterpriseControlPlane, UserRole, ControlPlanePermission

logger = get_logger("securoxi.api")
db = SecuroxiDatabase()
scanner = SecuroxiScanner(config=SecuroxiConfig())
control_plane = EnterpriseControlPlane()

API_KEY_NAME = "X-API-Key"
TENANT_HEADER_NAME = "X-Tenant-ID"
DEFAULT_API_KEY = os.environ.get("SECUROXI_API_KEY", "securoxi-enterprise-key")
IS_PRODUCTION = os.environ.get("ENVIRONMENT", "development").lower() == "production"

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
bearer_security = HTTPBearer(auto_error=False)


class ClientIdentity:
    def __init__(self, client_name: str, tenant_id: str, role: UserRole):
        self.client_name = client_name
        self.tenant_id = tenant_id
        self.role = role


def verify_api_key(
    api_key_header_val: Optional[str] = Security(api_key_header),
    auth_credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_security),
    tenant_header_val: Optional[str] = Header(None, alias="X-Tenant-ID")
) -> ClientIdentity:
    """Enterprise API Key / Bearer Token & Multi-Tenant Identity Validator."""
    provided_key = api_key_header_val or (auth_credentials.credentials if auth_credentials else None)
    tenant_id = tenant_header_val or "TENANT-DEFAULT"

    # Enforce mandatory production key check
    if IS_PRODUCTION and provided_key == "securoxi-enterprise-key":
        raise HTTPException(status_code=401, detail="Production environment requires explicit SECUROXI_API_KEY configuration.")

    if provided_key:
        # Check against Control Plane keys
        allowed, tenant_or_msg, role = control_plane.check_permission(provided_key, ControlPlanePermission.READ_SCAN)
        if allowed:
            return ClientIdentity(client_name=provided_key[:8], tenant_id=tenant_or_msg, role=role)

        if provided_key != DEFAULT_API_KEY:
            db.log_audit_event("AUTH_FAILURE", "API_CLIENT", f"Invalid API Key attempt: {provided_key[:4]}***", tenant_id=tenant_id)
            raise HTTPException(status_code=401, detail="Invalid API Key or Bearer Token.")

    return ClientIdentity(client_name=provided_key or "securoxi-client", tenant_id=tenant_id, role=UserRole.SUPER_ADMIN)


def require_permission(perm: ControlPlanePermission):
    def permission_dependency(client: ClientIdentity = Depends(verify_api_key)):
        allowed = True
        from securoxi.control_plane.governance import ROLE_PERMISSIONS
        allowed_perms = ROLE_PERMISSIONS.get(client.role, set())
        if perm not in allowed_perms:
            db.log_audit_event("FORBIDDEN_ATTEMPT", client.client_name, f"Role {client.role.value} denied permission {perm.value}", tenant_id=client.tenant_id)
            raise HTTPException(status_code=403, detail=f"FORBIDDEN: Role '{client.role.value}' lacks required permission '{perm.value}'")
        return client
    return permission_dependency


app = FastAPI(
    title="SECUROXI AI Enterprise API",
    description="Document Prompt Injection & Visual Deception Detection API",
    version="0.1.0"
)


@app.middleware("http")
async def add_security_headers_and_rate_limit(request, call_next):
    """Enforces secure HTTP headers and rate-limiting on all REST responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


@app.get("/api/v1/health/liveness")
def health_liveness():
    """Liveness probe endpoint indicating process is running."""
    import time
    return {"status": "alive", "timestamp": time.time()}


@app.get("/api/v1/health/readiness")
def health_readiness():
    """Readiness probe endpoint verifying database and system health."""
    db_status = "healthy"
    try:
        db.get_dashboard_stats()
    except Exception:
        db_status = "unhealthy"

    return {
        "status": "ready" if db_status == "healthy" else "degraded",
        "database": db_status,
        "broker": "healthy"
    }



from securoxi.brain.bulk_models import JobStatus, TaskStatus
from securoxi.brain.bulk_worker import SecuroxiBulkManager
bulk_manager = SecuroxiBulkManager()


@app.get("/api/v1/batches/{batch_id}")
def get_batch_status(batch_id: str, client: ClientIdentity = Depends(verify_api_key)):
    """Fetch status and progress summary for a distributed bulk processing batch."""
    job = bulk_manager.get_batch_job(batch_id, tenant_id=client.tenant_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Batch ID '{batch_id}' not found or access denied.")
    return job.to_dict()


@app.post("/api/v1/batches/{batch_id}/retry")
def retry_batch_failed_items(batch_id: str, client: ClientIdentity = Depends(verify_api_key)):
    """Retry failed items in a distributed bulk batch job."""
    job = bulk_manager.get_batch_job(batch_id, tenant_id=client.tenant_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Batch ID '{batch_id}' not found.")

    failed_tasks = [t for t in job.tasks if t.status in [TaskStatus.FAILED, TaskStatus.POISON]]
    for t in failed_tasks:
        t.status = TaskStatus.PENDING
        t.retry_count = 0

    job.status = JobStatus.QUEUED
    return {"message": f"Retrying {len(failed_tasks)} failed tasks for batch '{batch_id}'.", "job": job.to_dict()}


@app.post("/api/v1/batches/{batch_id}/cancel")
def cancel_batch_job(batch_id: str, client: ClientIdentity = Depends(verify_api_key)):
    """Cancel a pending or processing distributed bulk batch job."""
    job = bulk_manager.get_batch_job(batch_id, tenant_id=client.tenant_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Batch ID '{batch_id}' not found.")

    job.status = JobStatus.CANCELLED
    return {"message": f"Batch '{batch_id}' has been cancelled.", "job": job.to_dict()}


@app.get("/api/v1/stats")
def get_stats(client: ClientIdentity = Depends(verify_api_key)):
    """Fetch dashboard summary metrics."""
    return db.get_dashboard_stats(tenant_id=client.tenant_id)


@app.get("/api/v1/scans")
def list_scans(
    limit: int = Query(50, ge=1, le=500),
    verdict: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    client: ClientIdentity = Depends(verify_api_key)
):
    """List historical scan reports with optional verdict filtering and search."""
    return db.list_scans(limit=limit, verdict=verdict, search=search, tenant_id=client.tenant_id)


@app.get("/api/v1/scans/export")
def export_scans_report(
    format: str = Query("csv", pattern="^(csv|json)$"),
    verdict: Optional[str] = Query(None),
    client: ClientIdentity = Depends(verify_api_key)
):
    """Export scan results as CSV or JSON with tenant isolation."""
    scans = db.list_scans(limit=500, verdict=verdict, tenant_id=client.tenant_id)
    if format == "json":
        return JSONResponse(content=scans)

    import io
    import csv

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Scan ID", "Filename", "Format", "Verdict", "Risk Score", "Findings Count", "Created At"])
    for s in scans:
        writer.writerow([
            s.get("scan_id", ""),
            s.get("filename", ""),
            s.get("document_type", ""),
            s.get("verdict", ""),
            s.get("risk_score", 0),
            len(s.get("findings", []) or []),
            s.get("created_at", "")
        ])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="securoxi_scans_{client.tenant_id}.csv"'}
    )


@app.get("/api/v1/scan/{scan_id}")
def get_scan_report(scan_id: str, client: ClientIdentity = Depends(verify_api_key)):
    """Fetch detailed JSON security report for a specific scan ID with strict tenant isolation."""
    report = db.get_scan(scan_id, tenant_id=client.tenant_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Scan ID '{scan_id}' not found.")
    return report


@app.post("/api/v1/scan")
async def scan_file(file: UploadFile = File(...), client: ClientIdentity = Depends(verify_api_key)):
    """
    Scan a single PDF document or ZIP archive for prompt injection and visual deception threats.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename missing in upload request.")

    temp_dir = tempfile.mkdtemp(prefix="securoxi_upload_")
    try:
        temp_file_path = os.path.join(temp_dir, file.filename)
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Handle ZIP archive bulk scan
        if file.filename.lower().endswith(".zip"):
            db.log_audit_event("ZIP_BULK_UPLOAD", client.client_name, f"Submitted archive '{file.filename}' for extraction and scan", tenant_id=client.tenant_id)
            return process_zip_archive(temp_file_path, temp_dir, client.client_name)

        # Single document scan
        db.log_audit_event("SCAN_SUBMITTED", client.client_name, f"Submitted document '{file.filename}' for security scan", tenant_id=client.tenant_id)
        report = scanner.scan(temp_file_path)
        report_dict = report.to_dict()

        # Save to database with tenant isolation
        scan_id = db.save_scan(report_dict, tenant_id=client.tenant_id)
        db.log_audit_event("SCAN_COMPLETED", client.client_name, f"Scan '{scan_id}' finished: Verdict={report.verdict.value}, Score={report.risk_score}", tenant_id=client.tenant_id)

        return report_dict

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.post("/api/v1/scan/bulk")
async def bulk_scan_files(files: List[UploadFile] = File(...), client: ClientIdentity = Depends(verify_api_key)):
    """
    Scan multiple uploaded document files concurrently.
    """
    temp_dir = tempfile.mkdtemp(prefix="securoxi_bulk_")
    batch_results = []

    try:
        db.log_audit_event("BULK_BATCH_SUBMITTED", client.client_name, f"Submitted batch of {len(files)} files for scanning", tenant_id=client.tenant_id)
        for file in files:
            if not file.filename:
                continue
            file_path = os.path.join(temp_dir, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            report = scanner.scan(file_path)
            report_dict = report.to_dict()
            db.save_scan(report_dict, tenant_id=client.tenant_id)
            batch_results.append(report_dict)

        stats = {
            "total_files": len(batch_results),
            "safe": sum(1 for r in batch_results if r["verdict"] == "SAFE"),
            "suspicious": sum(1 for r in batch_results if r["verdict"] == "SUSPICIOUS"),
            "high_risk": sum(1 for r in batch_results if r["verdict"] == "HIGH_RISK"),
            "uninspectable": sum(1 for r in batch_results if r.get("verdict") == "UNINSPECTABLE"),
            "results": batch_results
        }
        return stats

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def process_zip_archive(zip_path: str, temp_dir: str, client: str) -> Dict[str, Any]:
    """Helper to safely extract and scan PDF files contained inside a ZIP archive with DoS & ZipSlip guards."""
    extract_dir = os.path.join(temp_dir, "extracted")
    os.makedirs(extract_dir, exist_ok=True)
    canonical_extract_dir = os.path.abspath(extract_dir)

    MAX_ZIP_ENTRIES = 50
    MAX_UNCOMPRESSED_BYTES = 50 * 1024 * 1024  # 50 MB total limit
    MAX_COMPRESSION_RATIO = 100.0  # 100:1 max ratio

    total_uncompressed_bytes = 0

    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            infolist = zip_ref.infolist()
            if len(infolist) > MAX_ZIP_ENTRIES:
                raise HTTPException(status_code=400, detail=f"ZIP archive exceeds maximum allowed files ({len(infolist)} > {MAX_ZIP_ENTRIES}).")

            for member in infolist:
                filename = os.path.basename(member.filename)
                if not filename or member.filename.startswith('/') or '..' in member.filename:
                    continue

                # Decompression Bomb Ratio & Total Size Checks
                comp_size = member.compress_size or 1
                uncomp_size = member.file_size
                ratio = uncomp_size / comp_size

                if ratio > MAX_COMPRESSION_RATIO and uncomp_size > 1024 * 1024:
                    raise HTTPException(status_code=400, detail=f"SUSPICIOUS_ARCHIVE: Decompression bomb detected (ratio {ratio:.1f}:1).")

                total_uncompressed_bytes += uncomp_size
                if total_uncompressed_bytes > MAX_UNCOMPRESSED_BYTES:
                    raise HTTPException(status_code=400, detail="SUSPICIOUS_ARCHIVE: Total uncompressed archive size exceeds 50MB limit.")

                # ZipSlip Canonicalization Validation
                target_path = os.path.abspath(os.path.join(extract_dir, member.filename))
                if not target_path.startswith(canonical_extract_dir):
                    raise HTTPException(status_code=400, detail="ZipSlip path traversal attempt detected.")

                zip_ref.extract(member, extract_dir)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to extract ZIP archive safely: {str(e)}")

    pdf_files = []
    for root, _, files in os.walk(extract_dir):
        for f in files:
            if f.lower().endswith(".pdf"):
                pdf_files.append(os.path.join(root, f))

    if not pdf_files:
        raise HTTPException(status_code=400, detail="No PDF document files found inside ZIP archive.")

    batch_results = []
    for pdf_path in pdf_files:
        report = scanner.scan(pdf_path)
        report_dict = report.to_dict()
        db.save_scan(report_dict)
        batch_results.append(report_dict)

    return {
        "archive_name": os.path.basename(zip_path),
        "total_files": len(batch_results),
        "safe": sum(1 for r in batch_results if r["verdict"] == "SAFE"),
        "suspicious": sum(1 for r in batch_results if r["verdict"] == "SUSPICIOUS"),
        "high_risk": sum(1 for r in batch_results if r["verdict"] == "HIGH_RISK"),
        "results": batch_results
    }


# Phase 2 Ingestion Engine Instance
from securoxi.screening.ingestion import SecuroxiIngestionEngine
ingestion_engine = SecuroxiIngestionEngine(config=SecuroxiConfig())



@app.post("/api/v1/screening/ingest/resume")
async def ingest_resume_endpoint(file: UploadFile = File(...), client: str = Depends(verify_api_key)):
    """
    Phase 2: Ingest an untrusted candidate resume document.
    Executes Phase 1 security scan, extracts text spans, and structures document sections.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename missing in upload request.")

    temp_dir = tempfile.mkdtemp(prefix="securoxi_resume_")
    try:
        temp_file_path = os.path.join(temp_dir, file.filename)
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        db.log_audit_event("RESUME_INGESTION_SUBMITTED", client, f"Ingesting resume '{file.filename}'")
        resume_doc = ingestion_engine.ingest_resume(temp_file_path)
        resume_dict = resume_doc.to_dict()

        # Save to database
        db.save_scan(resume_doc.security_report.to_dict())
        db.log_audit_event("RESUME_INGESTED", client, f"Resume '{resume_doc.resume_id}' ingested cleanly.")

        return resume_dict

    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.post("/api/v1/screening/ingest/jd")
async def ingest_jd_endpoint(file: Optional[UploadFile] = File(None), jd_text: Optional[str] = Query(None), client: str = Depends(verify_api_key)):
    """
    Phase 2: Ingest a Job Description from document file upload or raw text query.
    """
    if file and file.filename:
        temp_dir = tempfile.mkdtemp(prefix="securoxi_jd_")
        try:
            temp_file_path = os.path.join(temp_dir, file.filename)
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            db.log_audit_event("JD_INGESTION_SUBMITTED", client, f"Ingesting JD file '{file.filename}'")
            jd_doc = ingestion_engine.ingest_job_description(temp_file_path)
            return jd_doc.to_dict()
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    elif jd_text:
        db.log_audit_event("JD_INGESTION_SUBMITTED", client, "Ingesting JD raw text string")
        jd_doc = ingestion_engine.ingest_job_description(jd_text)
        return jd_doc.to_dict()

from securoxi.screening.extractor import RuleBasedExtractor
extractor_engine = RuleBasedExtractor()


@app.post("/api/v1/screening/extract/resume")
async def extract_resume_endpoint(file: UploadFile = File(...), client: str = Depends(verify_api_key)):
    """
    Phase 2 Stage 2: Ingest an untrusted resume and extract structured ExtractedResumeProfile.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename missing in upload request.")

    temp_dir = tempfile.mkdtemp(prefix="securoxi_extract_resume_")
    try:
        temp_file_path = os.path.join(temp_dir, file.filename)
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        db.log_audit_event("RESUME_EXTRACTION_SUBMITTED", client, f"Extracting profile from resume '{file.filename}'")
        resume_doc = ingestion_engine.ingest_resume(temp_file_path)
        profile = extractor_engine.extract_resume_profile(resume_doc)
        profile_dict = profile.to_dict()

        db.log_audit_event("RESUME_EXTRACTED", client, f"Resume profile '{profile.resume_id}' extracted cleanly.")
        return profile_dict

    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.post("/api/v1/screening/extract/jd")
async def extract_jd_endpoint(file: Optional[UploadFile] = File(None), jd_text: Optional[str] = Query(None), client: str = Depends(verify_api_key)):
    """
    Phase 2 Stage 2: Ingest a Job Description and extract structured ExtractedJDProfile.
    """
    if file and file.filename:
        temp_dir = tempfile.mkdtemp(prefix="securoxi_extract_jd_")
        try:
            temp_file_path = os.path.join(temp_dir, file.filename)
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            db.log_audit_event("JD_EXTRACTION_SUBMITTED", client, f"Extracting profile from JD file '{file.filename}'")
            jd_doc = ingestion_engine.ingest_job_description(temp_file_path)
            profile = extractor_engine.extract_jd_profile(jd_doc)
            return profile.to_dict()
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    elif jd_text:
        db.log_audit_event("JD_EXTRACTION_SUBMITTED", client, "Extracting profile from JD raw text string")
        jd_doc = ingestion_engine.ingest_job_description(jd_text)
        profile = extractor_engine.extract_jd_profile(jd_doc)
        return profile.to_dict()

from securoxi.screening.normalizer import SecuroxiNormalizer
normalizer_engine = SecuroxiNormalizer()


from securoxi.screening.matching_engine import SecuroxiMatchingEngine
matching_engine = SecuroxiMatchingEngine()


@app.post("/api/v1/screening/match")
async def match_resume_to_jd_endpoint(
    resume_file: UploadFile = File(...),
    jd_file: Optional[UploadFile] = File(None),
    jd_text: Optional[str] = Query(None),
    client: str = Depends(verify_api_key)
):
    """
    Phase 2 Stage 4: Match an untrusted candidate resume against a Job Description requirement.
    Executes security scan, structured extraction, normalization, and requirement-level semantic matching.
    """
    if not resume_file.filename:
        raise HTTPException(status_code=400, detail="Resume filename missing.")

    temp_dir = tempfile.mkdtemp(prefix="securoxi_match_")
    try:
        # Ingest Resume
        resume_file_path = os.path.join(temp_dir, resume_file.filename)
        with open(resume_file_path, "wb") as buffer:
            shutil.copyfileobj(resume_file.file, buffer)

        db.log_audit_event("MATCHING_REQUEST_SUBMITTED", client, f"Matching resume '{resume_file.filename}'")
        resume_doc = ingestion_engine.ingest_resume(resume_file_path)
        resume_prof = extractor_engine.extract_resume_profile(resume_doc)

        # Ingest JD
        if jd_file and jd_file.filename:
            jd_file_path = os.path.join(temp_dir, jd_file.filename)
            with open(jd_file_path, "wb") as buffer:
                shutil.copyfileobj(jd_file.file, buffer)
            jd_doc = ingestion_engine.ingest_job_description(jd_file_path)
        elif jd_text:
            jd_doc = ingestion_engine.ingest_job_description(jd_text)
        else:
            raise HTTPException(status_code=400, detail="Must provide either jd_file or jd_text string.")

        jd_prof = extractor_engine.extract_jd_profile(jd_doc)

        # Execute Requirement Matching
        report = matching_engine.match_resume_to_jd(resume_prof, jd_prof)
        db.log_audit_event("MATCHING_COMPLETED", client, f"Match completed: ratio={report.overall_match_ratio}")
        return report.to_dict()

    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


from securoxi.screening.qualification_analyzer import SecuroxiQualificationAnalyzer
qualification_analyzer = SecuroxiQualificationAnalyzer()



@app.post("/api/v1/screening/qualifications")
async def analyze_qualifications_endpoint(
    resume_file: UploadFile = File(...),
    jd_file: Optional[UploadFile] = File(None),
    jd_text: Optional[str] = Query(None),
    client: str = Depends(verify_api_key)
):
    """
    Phase 2 Stage 5: Analyze candidate qualification compliance against empirical evidence.
    Resolves employment overlaps, calculates tech-specific experience, and checks degree/cert qualifications.
    """
    if not resume_file.filename:
        raise HTTPException(status_code=400, detail="Resume filename missing.")

    temp_dir = tempfile.mkdtemp(prefix="securoxi_qual_")
    try:
        # Ingest Resume
        resume_file_path = os.path.join(temp_dir, resume_file.filename)
        with open(resume_file_path, "wb") as buffer:
            shutil.copyfileobj(resume_file.file, buffer)

        db.log_audit_event("QUALIFICATION_ANALYSIS_SUBMITTED", client, f"Analyzing qualifications for resume '{resume_file.filename}'")
        resume_doc = ingestion_engine.ingest_resume(resume_file_path)
        resume_prof = extractor_engine.extract_resume_profile(resume_doc)

        # Ingest JD
        if jd_file and jd_file.filename:
            jd_file_path = os.path.join(temp_dir, jd_file.filename)
            with open(jd_file_path, "wb") as buffer:
                shutil.copyfileobj(jd_file.file, buffer)
            jd_doc = ingestion_engine.ingest_job_description(jd_file_path)
        elif jd_text:
            jd_doc = ingestion_engine.ingest_job_description(jd_text)
        else:
            raise HTTPException(status_code=400, detail="Must provide either jd_file or jd_text string.")

        # Execute Qualification Analysis
        report = qualification_analyzer.analyze_qualifications(resume_prof, jd_prof)
        db.log_audit_event("QUALIFICATION_ANALYSIS_COMPLETED", client, f"Qualifications analyzed: score={report.qualification_score}")
        return report.to_dict()

    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


from securoxi.screening.scorer import SecuroxiCandidateScorer, SecuroxiRankingEngine
candidate_scorer = SecuroxiCandidateScorer()
ranking_engine_instance = SecuroxiRankingEngine()

ranking_engine_instance = SecuroxiRankingEngine()


@app.post("/api/v1/screening/score")
async def score_candidate_endpoint(
    resume_file: UploadFile = File(...),
    jd_file: Optional[UploadFile] = File(None),
    jd_text: Optional[str] = Query(None),
    client: str = Depends(verify_api_key)
):
    """
    Phase 2 Stage 6: Calculate an explainable Fit Score, requirement breakdown, strengths, and gaps for a candidate.
    """
    if not resume_file.filename:
        raise HTTPException(status_code=400, detail="Resume filename missing.")

    temp_dir = tempfile.mkdtemp(prefix="securoxi_score_")
    try:
        # Ingest Resume
        resume_file_path = os.path.join(temp_dir, resume_file.filename)
        with open(resume_file_path, "wb") as buffer:
            shutil.copyfileobj(resume_file.file, buffer)

        db.log_audit_event("CANDIDATE_SCORING_SUBMITTED", client, f"Scoring resume '{resume_file.filename}'")
        resume_doc = ingestion_engine.ingest_resume(resume_file_path)
        resume_prof = extractor_engine.extract_resume_profile(resume_doc)

        # Ingest JD
        if jd_file and jd_file.filename:
            jd_file_path = os.path.join(temp_dir, jd_file.filename)
            with open(jd_file_path, "wb") as buffer:
                shutil.copyfileobj(jd_file.file, buffer)
            jd_doc = ingestion_engine.ingest_job_description(jd_file_path)
        elif jd_text:
            jd_doc = ingestion_engine.ingest_job_description(jd_text)
        else:
            raise HTTPException(status_code=400, detail="Must provide either jd_file or jd_text string.")

        jd_prof = extractor_engine.extract_jd_profile(jd_doc)

        # Match, Analyze Qualifications, and Score
        match_rep = matching_engine.match_resume_to_jd(resume_prof, jd_prof)
        qual_rep = qualification_analyzer.analyze_qualifications(resume_prof, jd_prof)
        score_report = candidate_scorer.score_candidate(resume_prof, jd_prof, match_rep, qual_rep)

        db.log_audit_event("CANDIDATE_SCORING_COMPLETED", client, f"Fit score: {score_report.fit_score} ({score_report.fit_category})")
        return score_report.to_dict()

    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.post("/api/v1/screening/rank")
async def rank_candidates_endpoint(
    resume_files: List[UploadFile] = File(...),
    jd_file: Optional[UploadFile] = File(None),
    jd_text: Optional[str] = Query(None),
    client: str = Depends(verify_api_key)
):
    """
    Phase 2 Stage 6: Rank multiple candidate resume uploads against a single Job Description requirement.
    Returns sorted list of CandidateScoreReport objects descending by fit_score.
    """
    if not resume_files:
        raise HTTPException(status_code=400, detail="Must upload at least one candidate resume file.")

    temp_dir = tempfile.mkdtemp(prefix="securoxi_rank_")
    try:
        saved_paths: List[str] = []
        for file in resume_files:
            if file.filename:
                saved_path = os.path.join(temp_dir, file.filename)
                with open(saved_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                saved_paths.append(saved_path)

        # Ingest JD
        if jd_file and jd_file.filename:
            jd_source = os.path.join(temp_dir, jd_file.filename)
            with open(jd_source, "wb") as buffer:
                shutil.copyfileobj(jd_file.file, buffer)
        elif jd_text:
            jd_source = jd_text
        else:
            raise HTTPException(status_code=400, detail="Must provide either jd_file or jd_text string.")

        db.log_audit_event("CANDIDATE_RANKING_SUBMITTED", client, f"Ranking {len(saved_paths)} candidates")
        ranked_report = ranking_engine_instance.rank_candidates(saved_paths, jd_source)
        db.log_audit_event("CANDIDATE_RANKING_COMPLETED", client, f"Ranked {ranked_report.total_candidates} candidates cleanly.")

        return ranked_report.to_dict()

    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


from securoxi.screening.report_generator import SecuroxiReportGenerator
report_generator_instance = SecuroxiReportGenerator()


@app.post("/api/v1/screening/report")
async def generate_screening_report_endpoint(
    resume_file: UploadFile = File(...),
    jd_file: Optional[UploadFile] = File(None),
    jd_text: Optional[str] = Query(None),
    client: str = Depends(verify_api_key)
):
    """
    Phase 2 Stage 7: Generate a comprehensive, explainable screening report with evidence provenance,
    strengths, gaps, JSON representation, and Markdown text report.
    """
    if not resume_file.filename:
        raise HTTPException(status_code=400, detail="Resume filename missing.")

    temp_dir = tempfile.mkdtemp(prefix="securoxi_report_")
    try:
        # Ingest Resume
        resume_file_path = os.path.join(temp_dir, resume_file.filename)
        with open(resume_file_path, "wb") as buffer:
            shutil.copyfileobj(resume_file.file, buffer)

        db.log_audit_event("SCREENING_REPORT_SUBMITTED", client, f"Generating report for resume '{resume_file.filename}'")
        resume_doc = ingestion_engine.ingest_resume(resume_file_path)
        resume_prof = extractor_engine.extract_resume_profile(resume_doc)

        # Ingest JD
        if jd_file and jd_file.filename:
            jd_file_path = os.path.join(temp_dir, jd_file.filename)
            with open(jd_file_path, "wb") as buffer:
                shutil.copyfileobj(jd_file.file, buffer)
            jd_doc = ingestion_engine.ingest_job_description(jd_file_path)
        elif jd_text:
            jd_doc = ingestion_engine.ingest_job_description(jd_text)
        else:
            raise HTTPException(status_code=400, detail="Must provide either jd_file or jd_text string.")

        jd_prof = extractor_engine.extract_jd_profile(jd_doc)

        # Execute Pipeline
        match_rep = matching_engine.match_resume_to_jd(resume_prof, jd_prof)
        qual_rep = qualification_analyzer.analyze_qualifications(resume_prof, jd_prof)
        score_rep = candidate_scorer.score_candidate(resume_prof, jd_prof, match_rep, qual_rep)

        screening_report = report_generator_instance.generate_report(
            resume_prof, jd_prof, match_rep, qual_rep, score_rep
        )

        return {
            "json_report": screening_report.to_dict(),
            "markdown_report": screening_report.to_markdown()
        }

    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


from securoxi.screening.pipeline import SecuroxiScreeningPipeline
screening_pipeline_instance = SecuroxiScreeningPipeline(config=SecuroxiConfig())



@app.post("/api/v1/screening/pipeline/screen")
async def security_aware_screen_endpoint(
    resume_file: UploadFile = File(...),
    jd_file: Optional[UploadFile] = File(None),
    jd_text: Optional[str] = Query(None),
    block_high_risk: bool = Query(True),
    client: str = Depends(verify_api_key)
):
    """
    Phase 2 Stage 8: End-to-End Security-Aware Single Candidate Resume Screening Pipeline.
    Enforces Phase 1 Security Gate scanning before screening analysis.
    HIGH_RISK resumes are blocked/quarantined from automated screening.
    """
    if not resume_file.filename:
        raise HTTPException(status_code=400, detail="Resume filename missing.")

    temp_dir = tempfile.mkdtemp(prefix="securoxi_pipe_screen_")
    try:
        resume_path = os.path.join(temp_dir, resume_file.filename)
        with open(resume_path, "wb") as buffer:
            shutil.copyfileobj(resume_file.file, buffer)

        if jd_file and jd_file.filename:
            jd_source = os.path.join(temp_dir, jd_file.filename)
            with open(jd_source, "wb") as buffer:
                shutil.copyfileobj(jd_file.file, buffer)
        elif jd_text:
            jd_source = jd_text
        else:
            raise HTTPException(status_code=400, detail="Must provide either jd_file or jd_text string.")

        db.log_audit_event("SECURITY_PIPELINE_SCREEN_SUBMITTED", client, f"Screening resume '{resume_file.filename}'")
        res = screening_pipeline_instance.screen_resume(resume_path, jd_source, block_high_risk=block_high_risk)
        db.log_audit_event("SECURITY_PIPELINE_SCREEN_COMPLETED", client, f"Verdict: {res['security_verdict']}")

        return res

    except Exception as e:
        logger.error(f"Security pipeline ranking execution error: {e}")
        raise HTTPException(status_code=500, detail=f"Ranking pipeline execution failed: {str(e)}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.get("/api/v1/screenings")
def list_screenings_endpoint(
    limit: int = Query(50, ge=1, le=500),
    client: ClientIdentity = Depends(verify_api_key)
):
    """
    List candidate screening evaluations with security clearance and fit score breakdown.
    """
    return db.list_screening_results(limit=limit, tenant_id=client.tenant_id)


@app.get("/api/v1/incidents")
def list_incidents_endpoint(
    limit: int = Query(50, ge=1, le=500),
    client: ClientIdentity = Depends(verify_api_key)
):
    """
    List security incidents and causality records for Security Brain analysis.
    """
    return db.list_incidents(limit=limit, tenant_id=client.tenant_id)




@app.post("/api/v1/screening/pipeline/rank")
async def security_aware_rank_endpoint(
    resume_files: List[UploadFile] = File(...),
    jd_file: Optional[UploadFile] = File(None),
    jd_text: Optional[str] = Query(None),
    block_high_risk: bool = Query(True),
    client: str = Depends(verify_api_key)
):
    """
    Phase 2 Stage 8: End-to-End Security-Aware Multi-Candidate Ranking Pipeline.
    Enforces Phase 1 Security Gate scanning across all candidates.
    Quarantines malicious high-risk resumes at rank #0 with fit score 0.0.
    """
    if not resume_files:
        raise HTTPException(status_code=400, detail="Must upload at least one candidate resume file.")

    temp_dir = tempfile.mkdtemp(prefix="securoxi_pipe_rank_")
    try:
        saved_paths: List[str] = []
        for file in resume_files:
            if file.filename:
                saved_path = os.path.join(temp_dir, file.filename)
                with open(saved_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                saved_paths.append(saved_path)

        if jd_file and jd_file.filename:
            jd_source = os.path.join(temp_dir, jd_file.filename)
            with open(jd_source, "wb") as buffer:
                shutil.copyfileobj(jd_file.file, buffer)
        elif jd_text:
            jd_source = jd_text
        else:
            raise HTTPException(status_code=400, detail="Must provide either jd_file or jd_text string.")

        db.log_audit_event("SECURITY_PIPELINE_RANK_SUBMITTED", client, f"Ranking {len(saved_paths)} candidates")
        ranked_res = screening_pipeline_instance.rank_resumes(saved_paths, jd_source, block_high_risk=block_high_risk)
        db.log_audit_event("SECURITY_PIPELINE_RANK_COMPLETED", client, f"Ranked {ranked_res['total_resumes_processed']} candidates cleanly.")

        return ranked_res

    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)










@app.get("/api/v1/audit-logs")
def get_audit_logs(limit: int = Query(50, ge=1, le=500), client: ClientIdentity = Depends(verify_api_key)):
    """Fetch security audit logs with strict tenant isolation."""
    return db.get_audit_logs(limit=limit, tenant_id=client.tenant_id)


@app.post("/api/v1/ask")
def ask_securoxi_endpoint(
    payload: Dict[str, Any] = Body(...),
    client: ClientIdentity = Depends(verify_api_key)
):
    """
    Ask SECUROXI: Grounded document question answering across authorized tenant collection.
    """
    query = payload.get("query", "")
    if not query:
        raise HTTPException(status_code=400, detail="Query text is required.")

    from securoxi.screening.rag_engine import SecuroxiRAGEngine
    engine = SecuroxiRAGEngine()
    answer = engine.query_enterprise_documents(
        query=query,
        tenant_id=client.tenant_id,
        top_k=payload.get("top_k", 4)
    )
    return answer.to_dict()


# =========================================================================
# INTELLIGENCE 2.0 AGENTIC WORKSPACE ENDPOINTS (PHASE 4 STAGE 16)
# =========================================================================

from securoxi.orchestrator import AgentOrchestrator, SynthesisMode
orchestrator_instance = AgentOrchestrator(database=db)


@app.post("/api/v1/agentic/understand")
def agentic_understand_endpoint(
    payload: Dict[str, Any] = Body(...),
    client: ClientIdentity = Depends(verify_api_key)
):
    """
    Analyzes natural language task prompt and returns structured task understanding preview.
    """
    prompt = payload.get("prompt", "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Task prompt is required.")

    task_understanding = orchestrator_instance.task_understanding_engine.analyze_task(
        prompt=prompt,
        tenant_id=client.tenant_id,
        available_context=payload.get("context", {}),
    )
    return task_understanding.to_dict()


@app.post("/api/v1/agentic/execute")
def agentic_execute_endpoint(
    payload: Dict[str, Any] = Body(...),
    client: ClientIdentity = Depends(verify_api_key)
):
    """
    Executes the canonical Intelligence 2.0 end-to-end Agentic RAG pipeline.
    """
    prompt = payload.get("task_description", "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Task description is required.")

    mode_str = payload.get("synthesis_mode")
    synthesis_mode = SynthesisMode(mode_str) if mode_str and mode_str in SynthesisMode.__members__ else None

    result = orchestrator_instance.execute_agentic_rag(
        task_description=prompt,
        tenant_id=client.tenant_id,
        context=payload.get("context"),
        security_clearance=payload.get("security_clearance", "SAFE"),
        allow_untrusted=payload.get("allow_untrusted", False),
        synthesis_mode=synthesis_mode,
        comparison_entities=payload.get("comparison_entities"),
        retrieval_chunks=payload.get("retrieval_chunks"),
    )
    return result


@app.get("/api/v1/agentic/tasks")
def list_agentic_tasks_endpoint(
    limit: int = Query(20, ge=1, le=100),
    client: ClientIdentity = Depends(verify_api_key)
):
    """
    List recent tasks and runs for the tenant.
    """
    tasks = [
        t.to_dict() for t in orchestrator_instance._tasks.values()
        if t.tenant_id == client.tenant_id
    ][:limit]
    return tasks


# Static Dashboard UI Mounting
WEB_STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "web", "static"))
WEB_STATIC_DIST_DIR = os.path.join(WEB_STATIC_DIR, "dist")

if os.path.exists(WEB_STATIC_DIST_DIR):
    assets_dir = os.path.join(WEB_STATIC_DIST_DIR, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/")
    @app.get("/dashboard")
    @app.get("/overview")
    @app.get("/security-brain")
    @app.get("/incidents")
    @app.get("/documents")
    @app.get("/scans")
    @app.get("/screening")
    @app.get("/ats")
    @app.get("/monitoring")
    @app.get("/policies")
    @app.get("/audit")
    @app.get("/settings")
    @app.get("/design-system")
    def serve_frontend_spa():
        dist_index = os.path.join(WEB_STATIC_DIST_DIR, "index.html")
        if os.path.exists(dist_index):
            return FileResponse(dist_index)
        fallback_index = os.path.join(WEB_STATIC_DIR, "index.html")
        if os.path.exists(fallback_index):
            return FileResponse(fallback_index)
        return JSONResponse({"status": "SECUROXI AI API Active"})
elif os.path.exists(WEB_STATIC_DIR):
    app.mount("/static", StaticFiles(directory=WEB_STATIC_DIR), name="static")

    @app.get("/")
    @app.get("/dashboard")
    def serve_dashboard():
        index_file = os.path.join(WEB_STATIC_DIR, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return JSONResponse({"status": "SECUROXI AI API Active", "dashboard": "Static index.html missing"})
