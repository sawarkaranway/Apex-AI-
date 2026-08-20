"""
RAG Knowledge Base Tools (Hybrid Retrieval & Ingestion).
Wraps the multi-category hybrid search pipeline and document ingestion
into agent-callable tool contracts.
"""

from typing import List, Dict, Any, Optional
from ..rag_pipeline import (
    search_hybrid_knowledge,
    process_document_ingestion,
    format_grounded_context_fence,
    CATEGORIES
)


def search_knowledge_base(query: str, category: str = "all", top_k: int = 5) -> str:
    """
    Search the grounded Knowledge Base across User, Subject, Project, Uploaded, and System Knowledge.
    Returns relevance-scored knowledge excerpts with exact source citations (page & section).
    """
    if not query or not query.strip():
        return "Please provide a valid search query for the Knowledge Base."

    cat_filter = category.lower().strip() if category and category.lower() != "all" else None
    results = search_hybrid_knowledge(
        query=query,
        category=cat_filter,
        top_k=top_k,
        min_score_threshold=0.15
    )

    if not results:
        return f"No sufficiently relevant information was found in the Knowledge Base matching '{query}'."

    return format_grounded_context_fence(results)


def ingest_document(title: str, content: str, category: str = "user_knowledge", tags: Optional[List[str]] = None) -> str:
    """
    Ingest a new text document, note, or concept into the Knowledge Base with logical category assignment.
    Categories: user_knowledge, subject_knowledge, project_knowledge, uploaded_documents, system_knowledge.
    """
    if not title or not content:
        return "Error: Document title and content cannot be empty."

    valid_cat = category if category in CATEGORIES else "user_knowledge"

    try:
        from api.models import KnowledgeDocument
        doc = KnowledgeDocument.objects.create(
            title=title.strip(),
            category=valid_cat,
            content=content.strip(),
            document_type="text",
            tags=tags or [],
            status="processing"
        )
        success, msg = process_document_ingestion(str(doc.id))
        if success:
            return f"✅ Knowledge Document '{title}' successfully ingested and indexed into [{valid_cat}] ({doc.chunk_count} chunks, ID: {doc.id})."
        else:
            return f"⚠️ Ingestion warning for '{title}': {msg}"
    except Exception as e:
        return f"Database error creating Knowledge Document '{title}': {str(e)}"
