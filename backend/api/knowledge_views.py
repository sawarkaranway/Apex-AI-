"""
REST API Endpoints for Knowledge Base Management & Ingestion Pipeline.
Enforces:
- Tenant & User Isolation
- Read-only protection on system_knowledge for regular users
- Async background document ingestion
- Hybrid search testing & chunk inspection
"""

import os
import uuid
import threading
from django.conf import settings
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response

from .models import KnowledgeDocument, KnowledgeChunk
from agent.rag_pipeline import (
    process_document_ingestion,
    search_hybrid_knowledge,
    CATEGORIES
)

ALLOWED_FILE_EXTENSIONS = {'.pdf', '.docx', '.csv', '.xlsx', '.xls', '.pptx', '.txt', '.md', '.json'}
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB


def seed_system_knowledge():
    """Ensure core system/application knowledge documents exist."""
    try:
        if not KnowledgeDocument.objects.filter(is_system=True).exists():
            system_docs = [
                {
                    "title": "Chaitanya Karya — System Architecture & AI Capabilities",
                    "category": "system_knowledge",
                    "is_system": True,
                    "document_type": "system_reference",
                    "tags": ["architecture", "capabilities", "system"],
                    "content": (
                        "Chaitanya Karya is an autonomous desktop AI assistant featuring 39 deterministic tools, "
                        "a multi-tier memory architecture (Working, Episodic, Semantic Vector, Procedural Preferences), "
                        "an in-built Scientific Calculator with SymPy exact computation, and a production RAG Knowledge Base. "
                        "Background execution is supported via Windows System Tray, Global Hotkeys (Ctrl+Shift+Space, "
                        "Ctrl+Shift+K, Ctrl+Shift+W, Ctrl+Shift+E), and Wake Word acoustic listener ('Hey Chaitanya')."
                    )
                },
                {
                    "title": "Security Policy & Human-in-the-Loop Safeguards",
                    "category": "system_knowledge",
                    "is_system": True,
                    "document_type": "system_reference",
                    "tags": ["security", "policy", "approval"],
                    "content": (
                        "All tool actions adhere to deterministic policy classification in code. "
                        "Low-risk tools (reading files, mathematical calculations, web search, system metrics) execute autonomously. "
                        "High-risk tools (deleting files, sending external emails, scheduling calendar events, running shell commands, killing processes) "
                        "strictly require explicit human approval via interactive verification gates before execution."
                    )
                }
            ]
            for sd in system_docs:
                doc = KnowledgeDocument.objects.create(status="processing", **sd)
                process_document_ingestion(str(doc.id))
    except Exception:
        pass


@api_view(['GET'])
@permission_classes([AllowAny])
def list_knowledge_endpoint(request):
    """
    Lists Knowledge Documents with user isolation and category filtering.
    """
    seed_system_knowledge()
    user = request.user if request.user.is_authenticated else None
    category = request.query_params.get('category', 'all')
    search_q = request.query_params.get('search', '').strip()

    filter_q = Q(is_system=True)
    if user:
        filter_q |= Q(user=user) | Q(user__isnull=True)
    else:
        filter_q |= Q(user__isnull=True)

    if category and category != 'all':
        filter_q &= Q(category=category)

    if search_q:
        filter_q &= (Q(title__icontains=search_q) | Q(tags__icontains=search_q) | Q(content__icontains=search_q))

    docs = KnowledgeDocument.objects.filter(filter_q).order_by('-updated_at')

    data = [{
        'id': str(d.id),
        'title': d.title,
        'filename': d.filename,
        'category': d.category,
        'document_type': d.document_type,
        'file_type': d.file_type,
        'status': d.status,
        'chunk_count': d.chunk_count,
        'file_size': d.file_size,
        'tags': d.tags,
        'is_system': d.is_system,
        'error_message': d.error_message,
        'created_at': d.created_at.isoformat(),
        'updated_at': d.updated_at.isoformat()
    } for d in docs]

    return Response({
        'documents': data,
        'categories': CATEGORIES,
        'total_count': len(data)
    })


@api_view(['POST'])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser])
def upload_knowledge_file_endpoint(request):
    """
    Uploads a file (PDF, DOCX, CSV, XLSX, PPTX, TXT, MD) and triggers asynchronous ingestion.
    """
    if 'file' not in request.FILES:
        return Response({'error': 'No file uploaded.'}, status=status.HTTP_400_BAD_REQUEST)

    uploaded_file = request.FILES['file']
    category = request.data.get('category', 'uploaded_documents')
    if category not in CATEGORIES:
        category = 'uploaded_documents'

    # Normal users cannot upload directly to system_knowledge
    if category == 'system_knowledge' and not request.user.is_staff:
        category = 'uploaded_documents'

    title = request.data.get('title', uploaded_file.name).strip() or uploaded_file.name
    tags_raw = request.data.get('tags', '')
    tags = [t.strip() for t in tags_raw.split(',') if t.strip()] if isinstance(tags_raw, str) else tags_raw

    # Validate file extension
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    if ext not in ALLOWED_FILE_EXTENSIONS:
        return Response({
            'error': f"Unsupported file type '{ext}'. Supported formats: {', '.join(sorted(ALLOWED_FILE_EXTENSIONS))}"
        }, status=status.HTTP_400_BAD_REQUEST)

    # Validate size
    if uploaded_file.size > MAX_UPLOAD_SIZE:
        return Response({
            'error': f"File size exceeds 50MB limit ({uploaded_file.size / (1024*1024):.1f} MB)."
        }, status=status.HTTP_400_BAD_REQUEST)

    # Save file to disk
    save_dir = os.path.join(settings.BASE_DIR, 'media', 'knowledge_files')
    os.makedirs(save_dir, exist_ok=True)
    unique_filename = f"{uuid.uuid4().hex[:12]}_{uploaded_file.name}"
    file_path = os.path.join(save_dir, unique_filename)

    with open(file_path, 'wb+') as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)

    user = request.user if request.user.is_authenticated else None

    # Create document record in 'processing' status
    doc = KnowledgeDocument.objects.create(
        user=user,
        title=title,
        filename=uploaded_file.name,
        file_path=file_path,
        file_size=uploaded_file.size,
        file_type=ext.replace('.', ''),
        document_type='file_upload',
        category=category,
        tags=tags or [ext.replace('.', '')],
        status='processing'
    )

    # Trigger async ingestion worker in a background thread
    threading.Thread(target=process_document_ingestion, args=(str(doc.id),), daemon=True).start()

    return Response({
        'status': 'upload_complete',
        'message': f"File '{uploaded_file.name}' uploaded successfully. Background parsing and indexing in progress.",
        'document': {
            'id': str(doc.id),
            'title': doc.title,
            'filename': doc.filename,
            'category': doc.category,
            'status': doc.status
        }
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def create_knowledge_note_endpoint(request):
    """
    Creates a custom text note or subject knowledge entry and triggers ingestion.
    """
    title = request.data.get('title', '').strip()
    content = request.data.get('content', '').strip()
    category = request.data.get('category', 'user_knowledge')
    tags = request.data.get('tags', [])

    if not title or not content:
        return Response({'error': 'Title and content are required.'}, status=status.HTTP_400_BAD_REQUEST)

    if category not in CATEGORIES:
        category = 'user_knowledge'

    user = request.user if request.user.is_authenticated else None

    doc = KnowledgeDocument.objects.create(
        user=user,
        title=title,
        category=category,
        content=content,
        document_type='custom_note',
        tags=tags,
        status='processing'
    )

    # Trigger ingestion
    threading.Thread(target=process_document_ingestion, args=(str(doc.id),), daemon=True).start()

    return Response({
        'status': 'created',
        'document_id': str(doc.id),
        'title': doc.title,
        'category': doc.category
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_document_chunks_endpoint(request, doc_id):
    """
    Inspects all parsed semantic chunks and metadata for a given document.
    """
    try:
        doc = KnowledgeDocument.objects.get(id=doc_id)
    except KnowledgeDocument.DoesNotExist:
        return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)

    chunks = KnowledgeChunk.objects.filter(document=doc).order_by('chunk_index')
    data = [{
        'id': str(c.id),
        'chunk_index': c.chunk_index,
        'page_number': c.page_number,
        'section_title': c.section_title,
        'token_count': c.token_count,
        'text': c.text,
        'created_at': c.created_at.isoformat()
    } for c in chunks]

    return Response({
        'document': {
            'id': str(doc.id),
            'title': doc.title,
            'category': doc.category,
            'status': doc.status,
            'chunk_count': doc.chunk_count,
            'filename': doc.filename
        },
        'chunks': data
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def reindex_document_endpoint(request, doc_id):
    """
    Re-runs parsing and indexing on an existing Knowledge Document.
    """
    try:
        doc = KnowledgeDocument.objects.get(id=doc_id)
    except KnowledgeDocument.DoesNotExist:
        return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)

    doc.status = 'processing'
    doc.save(update_fields=['status'])

    threading.Thread(target=process_document_ingestion, args=(str(doc.id),), daemon=True).start()

    return Response({
        'status': 'reindexing_started',
        'document_id': str(doc.id),
        'message': f"Re-indexing triggered for '{doc.title}'."
    })


@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_document_endpoint(request, doc_id):
    """
    Deletes a Knowledge Document and cascades all indexed chunks.
    Blocks normal users from deleting system_knowledge documents.
    """
    try:
        doc = KnowledgeDocument.objects.get(id=doc_id)
    except KnowledgeDocument.DoesNotExist:
        return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)

    # Protect system knowledge
    if doc.is_system and not request.user.is_superuser:
        return Response({
            'error': 'System Knowledge documents are read-only and cannot be deleted by standard users.'
        }, status=status.HTTP_403_FORBIDDEN)

    # Clean up physical file if present
    if doc.file_path and os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception:
            pass

    doc.delete()
    return Response({'status': 'deleted', 'document_id': doc_id})


@api_view(['POST'])
@permission_classes([AllowAny])
def search_knowledge_endpoint(request):
    """
    Tests hybrid semantic + keyword retrieval with relevance score analysis.
    """
    query = request.data.get('query', '').strip()
    category = request.data.get('category', 'all')
    top_k = int(request.data.get('top_k', 5))

    if not query:
        return Response({'error': 'Query parameter is required.'}, status=status.HTTP_400_BAD_REQUEST)

    user_id = request.user.id if request.user.is_authenticated else None
    results = search_hybrid_knowledge(
        query=query,
        user_id=user_id,
        category=category,
        top_k=top_k
    )

    return Response({
        'query': query,
        'category': category,
        'results_count': len(results),
        'results': results
    })
