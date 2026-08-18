"""
SECUROXI AI Intelligence 2.0 — Retrieval & Research Agent Tools
Registers deterministic tools connected to the SecuroxiVectorStore, RAG Engine,
hybrid search, and citation resolver.
"""

from typing import Dict, Any, List, Optional
from securoxi.orchestrator.tools import ToolDefinition, ToolParameter, ToolRegistry
from securoxi.orchestrator.types import TrustLevel
from securoxi.orchestrator.context import ExecutionContext
from securoxi.storage.vector_store import SecuroxiVectorStore
from securoxi.screening.rag_engine import SecuroxiRAGEngine
from securoxi.logger import get_logger

logger = get_logger("orchestrator.retrieval_tools")


def register_retrieval_agent_tools(
    tool_registry: ToolRegistry,
    vector_store: Optional[SecuroxiVectorStore] = None,
    rag_engine: Optional[SecuroxiRAGEngine] = None,
):
    """Registers all authoritative retrieval tools into the ToolRegistry."""
    vstore = vector_store or SecuroxiVectorStore()
    rag = rag_engine or SecuroxiRAGEngine(vector_store=vstore)

    # 1. Vector Search Tool
    def _vector_search_handler(
        ctx: ExecutionContext,
        query: str = "",
        top_k: int = 5,
        min_score: float = 0.0,
        section_filter: Optional[str] = None,
        include_quarantined: bool = False
    ) -> Dict[str, Any]:
        logger.info(f"Executing Vector Search for '{query}' (Tenant: {ctx.tenant_id})")
        results = vstore.search(
            query=query,
            tenant_id=ctx.tenant_id,
            top_k=top_k,
            min_score=min_score,
            section_filter=section_filter,
            include_quarantined=include_quarantined,
        )
        return {
            "query": query,
            "tenant_id": ctx.tenant_id,
            "results_count": len(results),
            "hits": [r.to_dict() for r in results],
        }

    tool_registry.register(
        ToolDefinition(
            tool_id="vector_search",
            name="Vector Semantic Retrieval",
            description="Executes cosine similarity top-k semantic retrieval against tenant vector index",
            parameters=[
                ToolParameter(name="query", param_type="str", description="Search query string", required=True),
                ToolParameter(name="top_k", param_type="int", description="Max hits to return", required=False, default=5),
                ToolParameter(name="min_score", param_type="float", description="Minimum similarity score", required=False, default=0.0),
                ToolParameter(name="section_filter", param_type="str", description="Optional section heading filter", required=False),
                ToolParameter(name="include_quarantined", param_type="bool", description="Whether to include quarantined documents", required=False, default=False),
            ],
            trust_level=TrustLevel.LOW_RISK,
            handler=_vector_search_handler,
        )
    )

    # 2. Keyword Search Tool
    def _keyword_search_handler(
        ctx: ExecutionContext,
        keywords: List[str],
        top_k: int = 5,
        include_quarantined: bool = False
    ) -> Dict[str, Any]:
        logger.info(f"Executing Keyword Search for {keywords} (Tenant: {ctx.tenant_id})")
        hits = []
        if ctx.tenant_id in vstore._index:
            query_terms = [k.lower() for k in keywords]
            for record in vstore._index[ctx.tenant_id]:
                if not include_quarantined and record["security_status"] in ["HIGH_RISK", "UNINSPECTABLE"]:
                    continue
                text = record["chunk"].text.lower()
                match_count = sum(1 for term in query_terms if term in text)
                if match_count > 0:
                    hits.append({
                        "chunk_id": record["chunk_id"],
                        "document_id": record["document_id"],
                        "tenant_id": ctx.tenant_id,
                        "score": round(match_count / len(query_terms), 4),
                        "section_heading": record["section_heading"],
                        "text": record["chunk"].text,
                        "start_page": record["chunk"].start_page,
                        "end_page": record["chunk"].end_page,
                        "security_status": record["security_status"],
                        "matched_terms": [t for t in query_terms if t in text],
                    })
        hits.sort(key=lambda h: h["score"], reverse=True)
        return {
            "keywords": keywords,
            "tenant_id": ctx.tenant_id,
            "results_count": len(hits[:top_k]),
            "hits": hits[:top_k],
        }

    tool_registry.register(
        ToolDefinition(
            tool_id="keyword_search",
            name="Keyword Exact Match Search",
            description="Performs exact keyword and token presence filtering across indexed chunks",
            parameters=[
                ToolParameter(name="keywords", param_type="list", description="List of keyword terms to match", required=True),
                ToolParameter(name="top_k", param_type="int", description="Max hits to return", required=False, default=5),
                ToolParameter(name="include_quarantined", param_type="bool", description="Include quarantined documents", required=False, default=False),
            ],
            trust_level=TrustLevel.LOW_RISK,
            handler=_keyword_search_handler,
        )
    )

    # 3. Hybrid Search Tool
    def _hybrid_search_handler(
        ctx: ExecutionContext,
        query: str = "",
        keywords: Optional[List[str]] = None,
        top_k: int = 5,
        include_quarantined: bool = False
    ) -> Dict[str, Any]:
        logger.info(f"Executing Hybrid Search for '{query}' (Tenant: {ctx.tenant_id})")
        # Run vector search
        v_results = vstore.search(query=query, tenant_id=ctx.tenant_id, top_k=top_k * 2, include_quarantined=include_quarantined)
        v_map = {r.chunk.chunk_id: r for r in v_results}

        # Run keyword search if keywords provided
        kw_list = keywords or query.split()
        kw_results = _keyword_search_handler(ctx, keywords=kw_list, top_k=top_k * 2, include_quarantined=include_quarantined)["hits"]
        kw_map = {h["chunk_id"]: h for h in kw_results}

        all_chunk_ids = set(v_map.keys()).union(set(kw_map.keys()))
        combined_hits = []

        for cid in all_chunk_ids:
            v_hit = v_map.get(cid)
            kw_hit = kw_map.get(cid)

            v_score = v_hit.score if v_hit else 0.0
            kw_score = kw_hit["score"] if kw_hit else 0.0
            hybrid_score = round(0.6 * v_score + 0.4 * kw_score, 4)

            chunk = v_hit.chunk if v_hit else None
            text = chunk.text if chunk else kw_hit["text"]
            doc_id = v_hit.document_id if v_hit else kw_hit["document_id"]
            sec_status = v_hit.chunk.security_status if v_hit else kw_hit["security_status"]
            page = chunk.start_page if chunk else kw_hit["start_page"]
            heading = chunk.section_heading if chunk else kw_hit["section_heading"]

            combined_hits.append({
                "chunk_id": cid,
                "document_id": doc_id,
                "tenant_id": ctx.tenant_id,
                "score": hybrid_score,
                "vector_score": v_score,
                "keyword_score": kw_score,
                "text": text,
                "section_heading": heading,
                "page": page,
                "security_status": sec_status,
            })

        combined_hits.sort(key=lambda x: x["score"], reverse=True)
        return {
            "query": query,
            "tenant_id": ctx.tenant_id,
            "results_count": len(combined_hits[:top_k]),
            "hits": combined_hits[:top_k],
        }

    tool_registry.register(
        ToolDefinition(
            tool_id="hybrid_search",
            name="Hybrid Vector + Keyword Search",
            description="Combines dense vector similarity with sparse keyword matching for optimal recall",
            parameters=[
                ToolParameter(name="query", param_type="str", description="Search query string", required=True),
                ToolParameter(name="keywords", param_type="list", description="Optional keywords", required=False),
                ToolParameter(name="top_k", param_type="int", description="Max hits", required=False, default=5),
                ToolParameter(name="include_quarantined", param_type="bool", description="Include quarantined items", required=False, default=False),
            ],
            trust_level=TrustLevel.LOW_RISK,
            handler=_hybrid_search_handler,
        )
    )

    # 4. Rerank Evidence Tool
    def _rerank_handler(ctx: ExecutionContext, query: str = "", candidate_hits: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        hits = candidate_hits or []
        query_words = set(query.lower().split())
        for hit in hits:
            # Semantic relevance boost based on query keyword density
            text_words = set(hit.get("text", "").lower().split())
            overlap = len(query_words.intersection(text_words)) / max(len(query_words), 1)
            hit["rerank_score"] = round(0.5 * hit.get("score", 0.5) + 0.5 * overlap, 4)

        hits.sort(key=lambda h: h["rerank_score"], reverse=True)
        return {
            "query": query,
            "reranked_count": len(hits),
            "hits": hits,
        }

    tool_registry.register(
        ToolDefinition(
            tool_id="rerank_evidence",
            name="Evidence Reranker",
            description="Reranks candidate evidence chunks based on exact query alignment and keyword density",
            parameters=[
                ToolParameter(name="query", param_type="str", description="Query string", required=True),
                ToolParameter(name="candidate_hits", param_type="list", description="Hits to rerank", required=True),
            ],
            trust_level=TrustLevel.LOW_RISK,
            handler=_rerank_handler,
        )
    )
