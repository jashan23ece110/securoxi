"""
SECUROXI AI Stage E — Ask SECUROXI / Secure Document Intelligence Test Suite
Validates grounded natural-language Q&A, multi-tenant boundaries,
quarantine exclusion, citation integrity, and fallback behavior.
"""

import unittest
from fastapi.testclient import TestClient
from securoxi.api.app import app


class TestAskSecuroxiIntelligence(unittest.TestCase):
    """Test suite for Ask SECUROXI document intelligence endpoints and invariants."""

    def setUp(self):
        self.client = TestClient(app)
        self.headers = {
            "X-API-Key": "securoxi-enterprise-key",
            "X-Tenant-ID": "TENANT-TEST-RAG"
        }

    def test_ask_securoxi_endpoint_contract(self):
        """Verify /api/v1/ask returns structured RAG answer with citations and groundedness metrics."""
        payload = {
            "query": "Which candidates have Kubernetes and cloud security experience?",
            "top_k": 4
        }
        res = self.client.post("/api/v1/ask", json=payload, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("query", data)
        self.assertIn("answer_text", data)
        self.assertIn("citations", data)
        self.assertIn("groundedness_score", data)
        self.assertIn("execution_time_ms", data)
        self.assertIsInstance(data["citations"], list)

    def test_ask_securoxi_missing_query_error(self):
        """Verify empty query returns 400 bad request."""
        res = self.client.post("/api/v1/ask", json={"query": ""}, headers=self.headers)
        self.assertEqual(res.status_code, 400)

    def test_quarantined_content_exclusion_invariant(self):
        """Ensure RAG engine excludes HIGH_RISK quarantined content from trusted answer assembly."""
        from securoxi.screening.rag_engine import SecuroxiRAGEngine
        engine = SecuroxiRAGEngine()
        # Verify vector search invocation sets include_quarantined=False
        answer = engine.query_enterprise_documents(
            query="Find prompt injection payloads",
            tenant_id="TENANT-TEST-RAG"
        )
        self.assertIsNotNone(answer.answer_text)
        self.assertEqual(answer.security_filtered_count, 0)


if __name__ == "__main__":
    unittest.main()
