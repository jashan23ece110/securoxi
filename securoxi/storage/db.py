"""
SECUROXI AI Storage & Audit Trail Persistence Layer
Manages SQLite and PostgreSQL database storage for scan reports, historical metrics,
incidents, policies, API keys, screening results, and security audit logs.
"""

import sqlite3
import json
import os
import time
import re
from typing import Dict, Any, List, Optional, Union

DB_PATH = os.environ.get("SECUROXI_DB_PATH", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "securoxi.db")))
DATABASE_URL = os.environ.get("DATABASE_URL") or os.environ.get("SECUROXI_DB_URL")


class SecuroxiDatabase:
    """Production-grade Database manager supporting both SQLite (Development) and PostgreSQL (Production)."""

    def __init__(self, db_path: Optional[str] = None, database_url: Optional[str] = None):
        self.database_url = database_url or DATABASE_URL
        self.db_path = db_path or DB_PATH

        if self.database_url and (self.database_url.startswith("postgresql://") or self.database_url.startswith("postgres://")):
            self.dialect = "postgres"
        else:
            self.dialect = "sqlite"

        self._init_db()

    def _get_connection(self):
        """Establishes connection based on active dialect (SQLite or PostgreSQL)."""
        if self.dialect == "postgres":
            try:
                import psycopg2
                from psycopg2.extras import RealDictCursor
                conn = psycopg2.connect(self.database_url, cursor_factory=RealDictCursor)
                return conn
            except Exception:
                # Fallback to SQLite if psycopg2 or PostgreSQL driver unavailable in local test env
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                return conn
        else:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn

    def _init_db(self):
        """Initializes tables and indexes using dialect-compatible DDL."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            if self.dialect == "postgres" and type(conn).__module__.startswith("psycopg2"):
                # PostgreSQL DDL Schema
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS scans (
                        scan_id VARCHAR(255) PRIMARY KEY,
                        tenant_id VARCHAR(255) DEFAULT 'TENANT-DEFAULT',
                        filename VARCHAR(512) NOT NULL,
                        document_type VARCHAR(64) NOT NULL,
                        verdict VARCHAR(64) NOT NULL,
                        risk_score INTEGER NOT NULL,
                        primary_threat VARCHAR(255),
                        overall_confidence DOUBLE PRECISION NOT NULL,
                        report_json TEXT NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS audit_logs (
                        log_id VARCHAR(255) PRIMARY KEY,
                        tenant_id VARCHAR(255) DEFAULT 'TENANT-DEFAULT',
                        event_type VARCHAR(128) NOT NULL,
                        actor VARCHAR(255) NOT NULL,
                        details TEXT NOT NULL,
                        timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS incidents (
                        incident_id VARCHAR(255) PRIMARY KEY,
                        tenant_id VARCHAR(255) DEFAULT 'TENANT-DEFAULT',
                        severity VARCHAR(64) NOT NULL,
                        status VARCHAR(64) NOT NULL,
                        attack_type VARCHAR(128) NOT NULL,
                        affected_asset VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS policies (
                        policy_id VARCHAR(255) PRIMARY KEY,
                        tenant_id VARCHAR(255) DEFAULT 'TENANT-DEFAULT',
                        name VARCHAR(255) NOT NULL,
                        priority INTEGER NOT NULL,
                        action VARCHAR(64) NOT NULL,
                        condition TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS api_keys (
                        key_id VARCHAR(255) PRIMARY KEY,
                        tenant_id VARCHAR(255) DEFAULT 'TENANT-DEFAULT',
                        key_hash VARCHAR(255) NOT NULL,
                        user_id VARCHAR(255) NOT NULL,
                        role VARCHAR(64) NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS screening_results (
                        screening_id VARCHAR(255) PRIMARY KEY,
                        tenant_id VARCHAR(255) DEFAULT 'TENANT-DEFAULT',
                        candidate_id VARCHAR(255) NOT NULL,
                        job_id VARCHAR(255) NOT NULL,
                        fit_score DOUBLE PRECISION NOT NULL,
                        skill_match_pct DOUBLE PRECISION NOT NULL,
                        qualification_verdict VARCHAR(64) NOT NULL,
                        explanation TEXT NOT NULL,
                        security_clearance BOOLEAN NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                """)
            else:
                # SQLite DDL Schema
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS scans (
                        scan_id TEXT PRIMARY KEY,
                        tenant_id TEXT DEFAULT 'TENANT-DEFAULT',
                        filename TEXT NOT NULL,
                        document_type TEXT NOT NULL,
                        verdict TEXT NOT NULL,
                        risk_score INTEGER NOT NULL,
                        primary_threat TEXT,
                        overall_confidence REAL NOT NULL,
                        report_json TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS audit_logs (
                        log_id TEXT PRIMARY KEY,
                        tenant_id TEXT DEFAULT 'TENANT-DEFAULT',
                        event_type TEXT NOT NULL,
                        actor TEXT NOT NULL,
                        details TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS incidents (
                        incident_id TEXT PRIMARY KEY,
                        tenant_id TEXT DEFAULT 'TENANT-DEFAULT',
                        severity TEXT NOT NULL,
                        status TEXT NOT NULL,
                        attack_type TEXT NOT NULL,
                        affected_asset TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS policies (
                        policy_id TEXT PRIMARY KEY,
                        tenant_id TEXT DEFAULT 'TENANT-DEFAULT',
                        name TEXT NOT NULL,
                        priority INTEGER NOT NULL,
                        action TEXT NOT NULL,
                        condition TEXT NOT NULL
                    )
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS api_keys (
                        key_id TEXT PRIMARY KEY,
                        tenant_id TEXT DEFAULT 'TENANT-DEFAULT',
                        key_hash TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS screening_results (
                        screening_id TEXT PRIMARY KEY,
                        tenant_id TEXT DEFAULT 'TENANT-DEFAULT',
                        candidate_id TEXT NOT NULL,
                        job_id TEXT NOT NULL,
                        fit_score REAL NOT NULL,
                        skill_match_pct REAL NOT NULL,
                        qualification_verdict TEXT NOT NULL,
                        explanation TEXT NOT NULL,
                        security_clearance INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Schema migration checks for SQLite
                cursor.execute("PRAGMA table_info(scans)")
                scans_cols = [row[1] for row in cursor.fetchall()]
                if "tenant_id" not in scans_cols:
                    cursor.execute("ALTER TABLE scans ADD COLUMN tenant_id TEXT DEFAULT 'TENANT-DEFAULT'")

                cursor.execute("PRAGMA table_info(audit_logs)")
                audit_cols = [row[1] for row in cursor.fetchall()]
                if "tenant_id" not in audit_cols:
                    cursor.execute("ALTER TABLE audit_logs ADD COLUMN tenant_id TEXT DEFAULT 'TENANT-DEFAULT'")

            conn.commit()
        finally:
            conn.close()

    def _execute_query(self, query: str, params: tuple = ()) -> tuple:
        """Executes query translating placeholders and upserts for PostgreSQL compatibility."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            exec_query = query
            exec_params = params

            if self.dialect == "postgres" and type(conn).__module__.startswith("psycopg2"):
                # Translate ? to %s for psycopg2
                exec_query = exec_query.replace("?", "%s")

                # Translate INSERT OR REPLACE INTO scans
                if "INSERT OR REPLACE INTO scans" in exec_query:
                    exec_query = exec_query.replace(
                        "INSERT OR REPLACE INTO scans",
                        "INSERT INTO scans"
                    ) + " ON CONFLICT (scan_id) DO UPDATE SET tenant_id = EXCLUDED.tenant_id, filename = EXCLUDED.filename, document_type = EXCLUDED.document_type, verdict = EXCLUDED.verdict, risk_score = EXCLUDED.risk_score, primary_threat = EXCLUDED.primary_threat, overall_confidence = EXCLUDED.overall_confidence, report_json = EXCLUDED.report_json"

            cursor.execute(exec_query, exec_params)

            # Check if SELECT or returning query
            if exec_query.strip().upper().startswith("SELECT"):
                rows = cursor.fetchall()
                if type(conn).__module__.startswith("psycopg2"):
                    results = [dict(r) for r in rows]
                else:
                    results = [dict(r) for r in rows]
                conn.commit()
                return results, cursor.rowcount
            else:
                conn.commit()
                return [], cursor.rowcount
        finally:
            conn.close()

    def save_scan(self, report_dict: Dict[str, Any], tenant_id: str = "TENANT-DEFAULT") -> str:
        scan_id = report_dict.get("metadata", {}).get("scan_id") or f"SCAN-{os.urandom(4).hex()}"
        query = """
            INSERT OR REPLACE INTO scans 
            (scan_id, tenant_id, filename, document_type, verdict, risk_score, primary_threat, overall_confidence, report_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            scan_id,
            tenant_id,
            report_dict.get("filename", "unknown"),
            report_dict.get("document_type", "PDF"),
            report_dict.get("verdict", "SAFE"),
            report_dict.get("risk_score", 0),
            report_dict.get("primary_threat"),
            report_dict.get("overall_confidence", 1.0),
            json.dumps(report_dict)
        )
        self._execute_query(query, params)
        return scan_id

    def get_scan(self, scan_id: str, tenant_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if tenant_id:
            query = "SELECT report_json FROM scans WHERE scan_id = ? AND (tenant_id = ? OR tenant_id = 'TENANT-DEFAULT')"
            params = (scan_id, tenant_id)
        else:
            query = "SELECT report_json FROM scans WHERE scan_id = ?"
            params = (scan_id,)

        rows, _ = self._execute_query(query, params)
        if rows:
            data = json.loads(rows[0]["report_json"])
            if isinstance(data, dict):
                data.setdefault("scan_id", scan_id)
            return data
        return None

    def list_scans(self, limit: int = 50, verdict: Optional[str] = None, search: Optional[str] = None, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        query = "SELECT scan_id, tenant_id, filename, document_type, verdict, risk_score, primary_threat, overall_confidence, created_at FROM scans WHERE 1=1"
        params = []

        if tenant_id:
            query += " AND (tenant_id = ? OR tenant_id = 'TENANT-DEFAULT')"
            params.append(tenant_id)

        if verdict:
            query += " AND verdict = ?"
            params.append(verdict.upper())

        if search:
            query += " AND filename LIKE ?"
            params.append(f"%{search}%")

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        rows, _ = self._execute_query(query, tuple(params))
        return rows

    def get_dashboard_stats(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        t_filter = " WHERE (tenant_id = ? OR tenant_id = 'TENANT-DEFAULT')" if tenant_id else ""
        t_params = (tenant_id,) if tenant_id else ()

        total_rows, _ = self._execute_query(f"SELECT COUNT(*) as total FROM scans{t_filter}", t_params)
        total = total_rows[0]["total"] if total_rows else 0

        s_filter = f"{t_filter} AND verdict = 'SAFE'" if t_filter else " WHERE verdict = 'SAFE'"
        safe_rows, _ = self._execute_query(f"SELECT COUNT(*) as safe FROM scans{s_filter}", t_params)
        safe = safe_rows[0]["safe"] if safe_rows else 0

        sp_filter = f"{t_filter} AND verdict = 'SUSPICIOUS'" if t_filter else " WHERE verdict = 'SUSPICIOUS'"
        suspicious_rows, _ = self._execute_query(f"SELECT COUNT(*) as suspicious FROM scans{sp_filter}", t_params)
        suspicious = suspicious_rows[0]["suspicious"] if suspicious_rows else 0

        hr_filter = f"{t_filter} AND verdict = 'HIGH_RISK'" if t_filter else " WHERE verdict = 'HIGH_RISK'"
        high_risk_rows, _ = self._execute_query(f"SELECT COUNT(*) as high_risk FROM scans{hr_filter}", t_params)
        high_risk = high_risk_rows[0]["high_risk"] if high_risk_rows else 0

        avg_rows, _ = self._execute_query(f"SELECT AVG(risk_score) as avg_score FROM scans{t_filter}", t_params)
        avg_score = round(avg_rows[0]["avg_score"] or 0, 1) if avg_rows else 0.0

        return {
            "total_scans": total,
            "safe": safe,
            "suspicious": suspicious,
            "high_risk": high_risk,
            "avg_risk_score": avg_score
        }

    def log_audit_event(self, event_type: str, actor: str, details: str, tenant_id: str = "TENANT-DEFAULT"):
        import uuid
        log_id = f"LOG-{uuid.uuid4().hex[:8]}"
        query = "INSERT INTO audit_logs (log_id, tenant_id, event_type, actor, details) VALUES (?, ?, ?, ?, ?)"
        params = (log_id, tenant_id, event_type, actor, details)
        self._execute_query(query, params)

    def get_audit_logs(self, limit: int = 50, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if tenant_id:
            query = "SELECT * FROM audit_logs WHERE (tenant_id = ? OR tenant_id = 'TENANT-DEFAULT') ORDER BY timestamp DESC LIMIT ?"
            params = (tenant_id, limit)
        else:
            query = "SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT ?"
            params = (limit,)

        rows, _ = self._execute_query(query, params)
        return rows

    def purge_expired_data(self, retention_days: int = 90, tenant_id: Optional[str] = None) -> Dict[str, int]:
        """Purges scan reports and audit logs older than or equal to retention_days cutoff."""
        cutoff_date = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time() - (retention_days * 86400) + 1))
        scans_purged = 0
        logs_purged = 0

        if tenant_id:
            query_scans = "DELETE FROM scans WHERE created_at <= ? AND tenant_id = ?"
            _, scans_purged = self._execute_query(query_scans, (cutoff_date, tenant_id))

            query_logs = "DELETE FROM audit_logs WHERE timestamp <= ? AND tenant_id = ?"
            _, logs_purged = self._execute_query(query_logs, (cutoff_date, tenant_id))
        else:
            query_scans = "DELETE FROM scans WHERE created_at <= ?"
            _, scans_purged = self._execute_query(query_scans, (cutoff_date,))

            query_logs = "DELETE FROM audit_logs WHERE timestamp <= ?"
            _, logs_purged = self._execute_query(query_logs, (cutoff_date,))

        return {"scans_purged": max(0, scans_purged), "logs_purged": max(0, logs_purged)}
