# SECUROXI AI — Complete Enterprise AI Security & Screening Platform

[![Platform Status](https://img.shields.io/badge/Platform%20Status-PRODUCTION%20READY-brightgreen.svg)](#final-status)
[![Tests](https://img.shields.io/badge/Tests-226%2F226%20Passed-brightgreen.svg)](#test-results)
[![Database](https://img.shields.io/badge/Database-PostgreSQL%20%2B%20SQLite-blue.svg)](#database-architecture)
[![Event Bus](https://img.shields.io/badge/Event%20Bus-Redis%20Streams-red.svg)](#distributed-event-infrastructure)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](#license)

**SECUROXI AI** is an enterprise-grade AI security platform, Security-Aware Resume-to-JD Screening System, and Security Operations Center (SOC). It protects enterprise talent and data pipelines against indirect prompt injections, visual deception attacks, hidden text, ATS score manipulation, and data exfiltration threats while delivering explainable candidate screening, continuous threat monitoring, and automated policy enforcement.

---

## ⚠️ Security Notice & Considerations

> [!IMPORTANT]
> **SECUROXI AI is a defense-in-depth security platform. However, no software platform should ever be described as unhackable or perfectly secure.** Enterprise deployment requires adherence to secure network isolation, TLS encryption, strong API key rotation, and strict multi-tenant access control policies.

---

## 🌟 Key Subsystem Capabilities

* 👁️ **Phase 1: Document AI Security Engine**: Micro-text font inspection (`< 4.5pt`), white font color distance analysis (`#FFFFFF`), vector background matching, invisible Unicode character detection, and layout-aware text span parsing via PyMuPDF.
* 🛡️ **Phase 2: Security-Aware Resume-to-JD Screening**: Requirement-level semantic matching, skill taxonomy normalization, empirical career interval merging, and mandatory security gate clearance (quarantines malicious resumes at **Rank #0 with Fit Score 0.0**).
* 🧠 **Phase 3: Security Brain & Control Plane**: 7-stage correlation pipeline (Signal $\rightarrow$ Forensics $\rightarrow$ Detection $\rightarrow$ Attack Graph $\rightarrow$ Policy), runtime AI boundary inspectors, ATS adapters (Greenhouse, Lever), continuous monitoring event bus, and deterministic Policy Engine authority (**Policy Engine decision strictly overrides advisory LLM recommendations**).
* 🔒 **Phase 4: Security Hardening & Red-Team Audit**: SHA-256 API key hashing, server-side RBAC permissions, tenant-isolated queries (`WHERE tenant_id = ?`), `SecuroxiSSRFGuard` blocking private subnets & AWS IMDS (`169.254.169.254`), ZipSlip path canonicalization, compression ratio caps, retention purging, and 9/9 red-team attack scenarios passed.
* 💻 **Phase 5: Enterprise Frontend Architecture**: React 18 + TypeScript + Vite SPA mounted directly inside FastAPI (`securoxi/web/static/dist`). 11 grouped enterprise navigation routes (`/overview`, `/security-brain`, `/incidents`, `/scans`, `/screening`, `/ats`, `/monitoring`, `/policies`, `/audit`, `/settings`, `/design-system`), dark-first technical aesthetic, and real API integrations.
* 📄 **Document Intelligence & RAG**: Multi-format document ingestion (`PDF`, `DOCX`, `TXT`, `HTML`, `PNG/JPG`), PyMuPDF + Tesseract `OCREngine` fallback, uninspectable document security guarantee, dual-document chunking (`FORENSIC` vs `SEMANTIC`), 384d vector embeddings + pgvector storage, and XML-fenced (`<retrieved_evidence>`) Grounded RAG.

---

## 📊 Automated Test Suite Results

* **Total Test Suite**: **`226 / 226 PASSED (100%)`**
* **Security & Adversarial Tests**: **`42 / 42 PASSED`**
* **Document Intelligence & OCR Tests**: **`20 / 20 PASSED`**
* **PostgreSQL Integration Tests**: **`5 / 5 PASSED`**
* **Distributed Event Bus Tests**: **`5 / 5 PASSED`**

---

## 🚀 Quick Start

### 1. Installation & Local Development (SQLite & Memory Bus)
```bash
git clone https://github.com/securoxi/securoxi.git
cd securoxi
pip install -r requirements.txt

# Run pytest test suite (226 tests)
python3 -m pytest

# Launch local development server
python3 -m uvicorn securoxi.api.app:app --host 127.0.0.1 --port 8000
```
Open `http://127.0.0.1:8000` to view the SECUROXI Enterprise SPA Frontend.

### 2. Launch Production Stack (Docker Compose with PostgreSQL & Redis)
```bash
# Launch PostgreSQL 16, Redis 7, and SECUROXI Enterprise App
docker-compose up -d --build

# Verify container health
docker-compose ps
```

---

## 📄 Documentation Artifacts

* [`docs/FINAL_PRODUCT_ARCHITECTURE.md`](file:///Users/jashanpreetsingh/Downloads/SECUROXI/docs/FINAL_PRODUCT_ARCHITECTURE.md): Complete End-to-End System Architecture
* [`docs/SECUROXI_FINAL_PRODUCT_AUDIT.md`](file:///Users/jashanpreetsingh/Downloads/SECUROXI/docs/SECUROXI_FINAL_PRODUCT_AUDIT.md): Whole-Product Security & Architecture Audit Report
* [`docs/DOCUMENT_INTELLIGENCE_FINAL_SECURITY_AUDIT.md`](file:///Users/jashanpreetsingh/Downloads/SECUROXI/docs/DOCUMENT_INTELLIGENCE_FINAL_SECURITY_AUDIT.md): Document Intelligence & RAG Final Security Audit Report
* [`docs/DOCUMENT_INTELLIGENCE_STAGE_6_RAG.md`](file:///Users/jashanpreetsingh/Downloads/SECUROXI/docs/DOCUMENT_INTELLIGENCE_STAGE_6_RAG.md): Grounded RAG & Secure Contextual Reasoning Specification

---

## 🛡️ License

Distributed under the MIT License. See `LICENSE` for more information.
