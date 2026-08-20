/* ═══════════════════════════════════════════════════════════
   Knowledge Base Management Module — Chaitanya Karya
   Features:
   - Logical Category Separation (User, Subject, Project, Uploaded, System)
   - Drag & Drop Multi-Format File Ingestion (PDF, DOCX, CSV, XLSX, PPTX, TXT, MD)
   - Real-Time Status Tracker (Uploading → Processing → Indexing → Ready / Failed)
   - Hybrid Search Simulator & Similarity Score Meters
   - Chunk Inspector with Page & Section Attributions
   - Re-index & Secure Deletion (Protects System Knowledge)
   ═══════════════════════════════════════════════════════════ */

import React, { useState, useEffect, useRef } from 'react'
import api from '@/shared/lib/api'

interface KnowledgeDoc {
  id: string
  title: string
  filename: string
  category: string
  document_type: string
  file_type: string
  status: 'uploading' | 'processing' | 'indexing' | 'ready' | 'failed'
  chunk_count: number
  file_size: number
  tags: string[]
  is_system: boolean
  error_message?: string
  created_at: string
  updated_at: string
}

interface ChunkItem {
  id: string
  chunk_index: number
  page_number: number
  section_title: string
  token_count: number
  text: string
  created_at: string
}

interface SearchResult {
  chunk_id: string
  document_id: string
  document_title: string
  category: string
  page_number: number
  section_title: string
  relevance_score: number
  text: string
  tags: string[]
}

interface KnowledgeBaseModalProps {
  isOpen: boolean
  onClose: () => void
  onInsertContextToChat?: (text: string) => void
}

const CATEGORY_TABS = [
  { id: 'all', label: 'All Knowledge', icon: '📂' },
  { id: 'user_knowledge', label: 'User Knowledge', icon: '👤' },
  { id: 'subject_knowledge', label: 'Subject / Domain', icon: '🎓' },
  { id: 'project_knowledge', label: 'Project Notes', icon: '🚀' },
  { id: 'uploaded_documents', label: 'Uploaded Files', icon: '📄' },
  { id: 'system_knowledge', label: 'System Knowledge', icon: '🛡️' }
]

export default function KnowledgeBaseModal({ isOpen, onClose, onInsertContextToChat }: KnowledgeBaseModalProps) {
  const [activeCategory, setActiveCategory] = useState('all')
  const [documents, setDocuments] = useState<KnowledgeDoc[]>([])
  const [loading, setLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<SearchResult[]>([])
  const [isSearching, setIsSearching] = useState(false)

  // Chunk inspection state
  const [inspectingDoc, setInspectingDoc] = useState<KnowledgeDoc | null>(null)
  const [chunks, setChunks] = useState<ChunkItem[]>([])
  const [loadingChunks, setLoadingChunks] = useState(false)

  // Custom Note Creation State
  const [isCreatingNote, setIsCreatingNote] = useState(false)
  const [noteTitle, setNoteTitle] = useState('')
  const [noteContent, setNoteContent] = useState('')
  const [noteCategory, setNoteCategory] = useState('user_knowledge')
  const [noteTags, setNoteTags] = useState('')

  // Upload State
  const [isDragging, setIsDragging] = useState(false)
  const [uploadProgress, setUploadProgress] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Fetch Documents
  const loadDocuments = async () => {
    setLoading(true)
    try {
      const data = await api.get<{ documents: KnowledgeDoc[] }>(
        `/knowledge/?category=${activeCategory}${searchQuery ? `&search=${encodeURIComponent(searchQuery)}` : ''}`
      )
      setDocuments(data.documents || [])
    } catch (err) {
      console.warn('Failed to load knowledge documents:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isOpen) {
      loadDocuments()
    }
  }, [isOpen, activeCategory])

  // Periodic polling for processing documents
  useEffect(() => {
    if (!isOpen) return undefined
    const hasProcessing = documents.some((d) => d.status === 'processing' || d.status === 'indexing')
    if (hasProcessing) {
      const interval = setInterval(loadDocuments, 2500)
      return () => clearInterval(interval)
    }
    return undefined
  }, [isOpen, documents])

  if (!isOpen) return null

  // Search Hybrid Knowledge
  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults([])
      return
    }
    setIsSearching(true)
    try {
      const res = await api.post<{ results: SearchResult[] }>('/knowledge/search/', {
        query: searchQuery,
        category: activeCategory,
        top_k: 5
      })
      setSearchResults(res.results || [])
    } catch (err) {
      console.error('Hybrid search error:', err)
    } finally {
      setIsSearching(false)
    }
  }

  // Upload File
  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return
    const file = files[0]

    setUploadProgress(`Uploading ${file.name}...`)
    const formData = new FormData()
    formData.append('file', file)
    formData.append('category', activeCategory === 'all' || activeCategory === 'system_knowledge' ? 'uploaded_documents' : activeCategory)
    formData.append('title', file.name)

    try {
      await api.upload('/knowledge/upload/', formData)
      setUploadProgress(`File uploaded! Processing & indexing...`)
      setTimeout(() => setUploadProgress(null), 3000)
      loadDocuments()
    } catch (err: any) {
      setUploadProgress(`Upload error: ${err.message || 'Failed'}`)
      setTimeout(() => setUploadProgress(null), 4000)
    }
  }

  // Create Note
  const handleCreateNote = async () => {
    if (!noteTitle.trim() || !noteContent.trim()) return
    try {
      await api.post('/knowledge/create/', {
        title: noteTitle,
        content: noteContent,
        category: noteCategory,
        tags: noteTags.split(',').map((t) => t.trim()).filter(Boolean)
      })
      setIsCreatingNote(false)
      setNoteTitle('')
      setNoteContent('')
      setNoteTags('')
      loadDocuments()
    } catch (err) {
      console.error(err)
    }
  }

  // Inspect Chunks
  const handleInspect = async (doc: KnowledgeDoc) => {
    setInspectingDoc(doc)
    setLoadingChunks(true)
    try {
      const data = await api.get<{ chunks: ChunkItem[] }>(`/knowledge/${doc.id}/chunks/`)
      setChunks(data.chunks || [])
    } catch (err) {
      console.error(err)
    } finally {
      setLoadingChunks(false)
    }
  }

  // Reindex
  const handleReindex = async (docId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await api.post(`/knowledge/${docId}/reindex/`, {})
      loadDocuments()
    } catch (err) {
      console.error(err)
    }
  }

  // Delete Document
  const handleDelete = async (docId: string, isSystem: boolean, e: React.MouseEvent) => {
    e.stopPropagation()
    if (isSystem) {
      alert('System Knowledge is read-only and cannot be deleted.')
      return
    }
    if (!confirm('Are you sure you want to delete this document and all indexed vector chunks?')) return

    try {
      await api.delete(`/knowledge/${docId}/`)
      setDocuments((prev) => prev.filter((d) => d.id !== docId))
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.75)',
        backdropFilter: 'blur(8px)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 20
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: '100%',
          maxWidth: 960,
          maxHeight: '92vh',
          backgroundColor: 'var(--color-bg-secondary)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-lg, 16px)',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: '16px 24px',
            borderBottom: '1px solid var(--color-border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'var(--color-bg-tertiary)'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div
              style={{
                width: 36,
                height: 36,
                borderRadius: 'var(--radius-md, 8px)',
                background: 'linear-gradient(135deg, #10B981 0%, #3B82F6 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.2rem',
                color: '#fff'
              }}
            >
              📚
            </div>
            <div>
              <h2 style={{ fontSize: '1.1rem', fontWeight: 700, margin: 0, color: 'var(--color-text-primary)' }}>
                Knowledge Base & Grounded RAG
              </h2>
              <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                Tenant-Isolated Multi-Category Persistent Information Layer
              </span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <button
              onClick={() => setIsCreatingNote(true)}
              style={{
                padding: '6px 14px',
                borderRadius: 8,
                border: '1px solid var(--color-border)',
                background: 'var(--color-bg-primary)',
                color: 'var(--color-text-primary)',
                fontSize: '0.8rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 6
              }}
            >
              ✍️ Add Note
            </button>

            <button
              onClick={() => fileInputRef.current?.click()}
              style={{
                padding: '6px 14px',
                borderRadius: 8,
                border: 'none',
                background: 'var(--color-accent)',
                color: '#fff',
                fontSize: '0.8rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 6
              }}
            >
              📤 Upload File
            </button>
            <input
              type="file"
              ref={fileInputRef}
              style={{ display: 'none' }}
              onChange={(e) => handleFileUpload(e.target.files)}
              accept=".pdf,.docx,.csv,.xlsx,.xls,.pptx,.txt,.md,.json"
            />

            <button
              onClick={onClose}
              style={{
                width: 32,
                height: 32,
                borderRadius: '50%',
                border: 'none',
                background: 'transparent',
                color: 'var(--color-text-muted)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.2rem'
              }}
            >
              ✕
            </button>
          </div>
        </div>

        {/* Category Tabs */}
        <div
          style={{
            display: 'flex',
            padding: '10px 24px 0',
            gap: 6,
            borderBottom: '1px solid var(--color-border)',
            background: 'var(--color-bg-tertiary)',
            overflowX: 'auto'
          }}
        >
          {CATEGORY_TABS.map((tab) => {
            const isActive = activeCategory === tab.id
            return (
              <button
                key={tab.id}
                onClick={() => {
                  setActiveCategory(tab.id)
                  setSearchResults([])
                }}
                style={{
                  padding: '8px 14px',
                  borderRadius: '8px 8px 0 0',
                  border: 'none',
                  borderBottom: isActive ? '2px solid var(--color-accent)' : '2px solid transparent',
                  background: isActive ? 'var(--color-bg-secondary)' : 'transparent',
                  color: isActive ? 'var(--color-text-primary)' : 'var(--color-text-secondary)',
                  fontSize: '0.8125rem',
                  fontWeight: isActive ? 600 : 500,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  transition: 'all 0.15s'
                }}
              >
                <span>{tab.icon}</span>
                <span>{tab.label}</span>
                {tab.id === 'system_knowledge' && (
                  <span style={{ fontSize: '0.65rem', padding: '1px 5px', borderRadius: 4, background: 'rgba(59, 130, 246, 0.2)', color: '#38BDF8' }}>
                    Read-Only
                  </span>
                )}
              </button>
            )
          })}
        </div>

        {/* Body Container */}
        <div style={{ flex: 1, overflowY: 'auto', padding: 24, display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Upload Progress Banner */}
          {uploadProgress && (
            <div
              style={{
                padding: '10px 16px',
                borderRadius: 8,
                background: 'rgba(56, 189, 248, 0.12)',
                border: '1px solid rgba(56, 189, 248, 0.3)',
                color: '#38BDF8',
                fontSize: '0.85rem',
                display: 'flex',
                alignItems: 'center',
                gap: 8
              }}
            >
              <span>⏳</span>
              <span>{uploadProgress}</span>
            </div>
          )}

          {/* Search & Ingestion Bar */}
          <div style={{ display: 'flex', gap: 10 }}>
            <div style={{ flex: 1, position: 'relative' }}>
              <input
                type="text"
                placeholder={`Search ${CATEGORY_TABS.find((t) => t.id === activeCategory)?.label}... (e.g. sentiment analysis, model accuracy)`}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                style={{
                  width: '100%',
                  padding: '10px 14px 10px 36px',
                  borderRadius: 8,
                  background: 'var(--color-bg-primary)',
                  border: '1px solid var(--color-border)',
                  color: 'var(--color-text-primary)',
                  fontSize: '0.875rem',
                  outline: 'none'
                }}
              />
              <span style={{ position: 'absolute', left: 12, top: 10, color: 'var(--color-text-muted)' }}>🔍</span>
            </div>

            <button
              onClick={handleSearch}
              disabled={isSearching || !searchQuery.trim()}
              style={{
                padding: '0 20px',
                borderRadius: 8,
                border: 'none',
                background: 'var(--color-accent)',
                color: '#fff',
                fontWeight: 600,
                fontSize: '0.85rem',
                cursor: isSearching || !searchQuery.trim() ? 'not-allowed' : 'pointer',
                opacity: isSearching || !searchQuery.trim() ? 0.6 : 1
              }}
            >
              {isSearching ? 'Searching...' : 'Hybrid Search'}
            </button>

            {searchResults.length > 0 && (
              <button
                onClick={() => setSearchResults([])}
                style={{
                  padding: '0 14px',
                  borderRadius: 8,
                  border: '1px solid var(--color-border)',
                  background: 'transparent',
                  color: 'var(--color-text-muted)',
                  fontSize: '0.8rem',
                  cursor: 'pointer'
                }}
              >
                Clear Search
              </button>
            )}
          </div>

          {/* Hybrid Search Results Preview */}
          {searchResults.length > 0 && (
            <div
              style={{
                padding: 16,
                borderRadius: 12,
                background: 'var(--color-bg-primary)',
                border: '1px solid var(--color-accent)',
                display: 'flex',
                flexDirection: 'column',
                gap: 12
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#38BDF8' }}>
                  🎯 Retrieved {searchResults.length} Grounded Knowledge Chunks
                </span>
                <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                  BM25 Lexical + Dense Vector Cosine Similarity
                </span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {searchResults.map((res, i) => (
                  <div
                    key={i}
                    style={{
                      padding: 12,
                      borderRadius: 8,
                      background: 'var(--color-bg-secondary)',
                      border: '1px solid var(--color-border)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 6
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>
                          📄 {res.document_title}
                        </span>
                        <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                          • Page {res.page_number} ({res.section_title})
                        </span>
                      </div>
                      <span
                        style={{
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          padding: '2px 8px',
                          borderRadius: 12,
                          background: res.relevance_score > 0.6 ? 'rgba(16, 185, 129, 0.2)' : 'rgba(56, 189, 248, 0.2)',
                          color: res.relevance_score > 0.6 ? '#10B981' : '#38BDF8'
                        }}
                      >
                        Score: {(res.relevance_score * 100).toFixed(0)}%
                      </span>
                    </div>

                    <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>
                      "{res.text}"
                    </div>

                    {onInsertContextToChat && (
                      <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 4 }}>
                        <button
                          onClick={() => {
                            onInsertContextToChat(`[Grounded Context from ${res.document_title}, Page ${res.page_number}]:\n"${res.text}"`)
                            onClose()
                          }}
                          style={{
                            padding: '4px 10px',
                            borderRadius: 6,
                            border: 'none',
                            background: 'rgba(56, 189, 248, 0.15)',
                            color: '#38BDF8',
                            fontSize: '0.75rem',
                            cursor: 'pointer'
                          }}
                        >
                          Use in Chat Prompt ↵
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Drag and Drop Zone */}
          <div
            onDragOver={(e) => {
              e.preventDefault()
              setIsDragging(true)
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={(e) => {
              e.preventDefault()
              setIsDragging(false)
              handleFileUpload(e.dataTransfer.files)
            }}
            onClick={() => fileInputRef.current?.click()}
            style={{
              padding: '24px 16px',
              border: `2px dashed ${isDragging ? 'var(--color-accent)' : 'var(--color-border)'}`,
              borderRadius: 12,
              background: isDragging ? 'rgba(56, 189, 248, 0.05)' : 'var(--color-bg-primary)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 8,
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            <span style={{ fontSize: '1.8rem' }}>📁</span>
            <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>
              Drag & Drop PDF, DOCX, CSV, XLSX, PPTX, TXT, or MD files here
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
              Files are automatically parsed, sanitized, chunked, and indexed with hybrid vector scoring.
            </div>
          </div>

          {/* Documents Grid / List */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-text-secondary)' }}>
                Ingested Knowledge Items ({documents.length})
              </span>
              <button
                onClick={loadDocuments}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--color-text-muted)',
                  fontSize: '0.75rem',
                  cursor: 'pointer'
                }}
              >
                🔄 Refresh
              </button>
            </div>

            {loading ? (
              <div style={{ textAlign: 'center', padding: 30, color: 'var(--color-text-muted)' }}>
                Loading knowledge documents...
              </div>
            ) : documents.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 40, color: 'var(--color-text-muted)' }}>
                No knowledge documents found in this category. Upload a file or add a note to get started.
              </div>
            ) : (
              documents.map((doc) => (
                <div
                  key={doc.id}
                  onClick={() => handleInspect(doc)}
                  style={{
                    padding: 14,
                    borderRadius: 10,
                    background: 'var(--color-bg-primary)',
                    border: '1px solid var(--color-border)',
                    cursor: 'pointer',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    transition: 'border-color 0.15s'
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--color-accent)')}
                  onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--color-border)')}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <div
                      style={{
                        width: 38,
                        height: 38,
                        borderRadius: 8,
                        background: 'var(--color-bg-tertiary)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '1.1rem'
                      }}
                    >
                      {doc.file_type === 'pdf' ? '📕' : doc.file_type === 'docx' ? '📘' : doc.file_type === 'csv' || doc.file_type === 'xlsx' ? '📊' : '📝'}
                    </div>

                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>
                          {doc.title}
                        </span>
                        {doc.is_system && (
                          <span style={{ fontSize: '0.65rem', padding: '2px 6px', borderRadius: 4, background: 'rgba(59, 130, 246, 0.2)', color: '#38BDF8' }}>
                            System
                          </span>
                        )}
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 4, fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                        <span style={{ textTransform: 'capitalize' }}>{doc.category.replace('_', ' ')}</span>
                        <span>•</span>
                        <span>{doc.chunk_count} Chunks</span>
                        {doc.file_size > 0 && (
                          <>
                            <span>•</span>
                            <span>{(doc.file_size / 1024).toFixed(1)} KB</span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    {/* Status Badge */}
                    <span
                      style={{
                        fontSize: '0.72rem',
                        fontWeight: 600,
                        padding: '3px 8px',
                        borderRadius: 10,
                        background:
                          doc.status === 'ready'
                            ? 'rgba(16, 185, 129, 0.15)'
                            : doc.status === 'failed'
                            ? 'rgba(239, 68, 68, 0.15)'
                            : 'rgba(245, 158, 11, 0.15)',
                        color:
                          doc.status === 'ready'
                            ? '#10B981'
                            : doc.status === 'failed'
                            ? '#EF4444'
                            : '#F59E0B'
                      }}
                    >
                      {doc.status.toUpperCase()}
                    </span>

                    {/* Actions */}
                    <button
                      onClick={(e) => handleReindex(doc.id, e)}
                      title="Re-index document"
                      style={{
                        padding: '4px 8px',
                        borderRadius: 6,
                        border: '1px solid var(--color-border)',
                        background: 'transparent',
                        color: 'var(--color-text-secondary)',
                        fontSize: '0.75rem',
                        cursor: 'pointer'
                      }}
                    >
                      Re-index
                    </button>

                    {!doc.is_system && (
                      <button
                        onClick={(e) => handleDelete(doc.id, doc.is_system, e)}
                        title="Delete document"
                        style={{
                          padding: '4px 8px',
                          borderRadius: 6,
                          border: '1px solid var(--color-border)',
                          background: 'transparent',
                          color: '#EF4444',
                          fontSize: '0.75rem',
                          cursor: 'pointer'
                        }}
                      >
                        Delete
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Chunk Inspection Modal */}
        {inspectingDoc && (
          <div
            style={{
              position: 'fixed',
              inset: 0,
              backgroundColor: 'rgba(0, 0, 0, 0.8)',
              backdropFilter: 'blur(6px)',
              zIndex: 10000,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: 20
            }}
            onClick={() => setInspectingDoc(null)}
          >
            <div
              style={{
                width: '100%',
                maxWidth: 780,
                maxHeight: '85vh',
                backgroundColor: 'var(--color-bg-secondary)',
                border: '1px solid var(--color-border)',
                borderRadius: 14,
                display: 'flex',
                flexDirection: 'column',
                overflow: 'hidden'
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <div
                style={{
                  padding: '16px 20px',
                  borderBottom: '1px solid var(--color-border)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  background: 'var(--color-bg-tertiary)'
                }}
              >
                <div>
                  <h3 style={{ margin: 0, fontSize: '1rem', color: 'var(--color-text-primary)' }}>
                    Chunk Inspection: {inspectingDoc.title}
                  </h3>
                  <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                    {chunks.length} semantic chunks generated for RAG vector retrieval
                  </span>
                </div>
                <button
                  onClick={() => setInspectingDoc(null)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: 'var(--color-text-muted)',
                    fontSize: '1.2rem',
                    cursor: 'pointer'
                  }}
                >
                  ✕
                </button>
              </div>

              <div style={{ flex: 1, overflowY: 'auto', padding: 20, display: 'flex', flexDirection: 'column', gap: 12 }}>
                {loadingChunks ? (
                  <div style={{ textAlign: 'center', padding: 40, color: 'var(--color-text-muted)' }}>
                    Loading chunks...
                  </div>
                ) : chunks.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: 40, color: 'var(--color-text-muted)' }}>
                    No chunks available for this document.
                  </div>
                ) : (
                  chunks.map((c) => (
                    <div
                      key={c.id}
                      style={{
                        padding: 14,
                        borderRadius: 8,
                        background: 'var(--color-bg-primary)',
                        border: '1px solid var(--color-border)',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: 6
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#38BDF8' }}>
                        <span>
                          Chunk #{c.chunk_index} • Page {c.page_number} ({c.section_title})
                        </span>
                        <span>{c.token_count} Tokens</span>
                      </div>
                      <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', lineHeight: 1.5, whiteSpace: 'pre-wrap' }}>
                        {c.text}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        {/* Add Note Modal */}
        {isCreatingNote && (
          <div
            style={{
              position: 'fixed',
              inset: 0,
              backgroundColor: 'rgba(0, 0, 0, 0.8)',
              backdropFilter: 'blur(6px)',
              zIndex: 10000,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: 20
            }}
            onClick={() => setIsCreatingNote(false)}
          >
            <div
              style={{
                width: '100%',
                maxWidth: 600,
                backgroundColor: 'var(--color-bg-secondary)',
                border: '1px solid var(--color-border)',
                borderRadius: 14,
                display: 'flex',
                flexDirection: 'column',
                overflow: 'hidden'
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <div
                style={{
                  padding: '16px 20px',
                  borderBottom: '1px solid var(--color-border)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  background: 'var(--color-bg-tertiary)'
                }}
              >
                <h3 style={{ margin: 0, fontSize: '1rem', color: 'var(--color-text-primary)' }}>
                  Add Note to Knowledge Base
                </h3>
                <button
                  onClick={() => setIsCreatingNote(false)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: 'var(--color-text-muted)',
                    fontSize: '1.2rem',
                    cursor: 'pointer'
                  }}
                >
                  ✕
                </button>
              </div>

              <div style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 14 }}>
                <div>
                  <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)' }}>
                    Note Title
                  </label>
                  <input
                    type="text"
                    placeholder="e.g., NewsLens Sentiment Model Architecture"
                    value={noteTitle}
                    onChange={(e) => setNoteTitle(e.target.value)}
                    style={{
                      width: '100%',
                      marginTop: 4,
                      padding: '10px 12px',
                      borderRadius: 8,
                      background: 'var(--color-bg-primary)',
                      border: '1px solid var(--color-border)',
                      color: 'var(--color-text-primary)',
                      fontSize: '0.875rem'
                    }}
                  />
                </div>

                <div>
                  <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)' }}>
                    Logical Category
                  </label>
                  <select
                    value={noteCategory}
                    onChange={(e) => setNoteCategory(e.target.value)}
                    style={{
                      width: '100%',
                      marginTop: 4,
                      padding: '10px 12px',
                      borderRadius: 8,
                      background: 'var(--color-bg-primary)',
                      border: '1px solid var(--color-border)',
                      color: 'var(--color-text-primary)',
                      fontSize: '0.875rem'
                    }}
                  >
                    <option value="user_knowledge">User Knowledge (Personal Facts / Preferences)</option>
                    <option value="subject_knowledge">Subject Knowledge (Data Science / ML / Tech Notes)</option>
                    <option value="project_knowledge">Project Knowledge (Codebase & Workflows)</option>
                    <option value="uploaded_documents">Uploaded Documents</option>
                  </select>
                </div>

                <div>
                  <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)' }}>
                    Note Content
                  </label>
                  <textarea
                    rows={6}
                    placeholder="Enter factual notes, formulas, project documentation, or long-term preferences..."
                    value={noteContent}
                    onChange={(e) => setNoteContent(e.target.value)}
                    style={{
                      width: '100%',
                      marginTop: 4,
                      padding: '10px 12px',
                      borderRadius: 8,
                      background: 'var(--color-bg-primary)',
                      border: '1px solid var(--color-border)',
                      color: 'var(--color-text-primary)',
                      fontSize: '0.875rem',
                      resize: 'vertical'
                    }}
                  />
                </div>

                <div>
                  <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)' }}>
                    Tags (comma-separated)
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. transformers, vader, ml, accuracy"
                    value={noteTags}
                    onChange={(e) => setNoteTags(e.target.value)}
                    style={{
                      width: '100%',
                      marginTop: 4,
                      padding: '8px 12px',
                      borderRadius: 8,
                      background: 'var(--color-bg-primary)',
                      border: '1px solid var(--color-border)',
                      color: 'var(--color-text-primary)',
                      fontSize: '0.85rem'
                    }}
                  />
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 10 }}>
                  <button
                    onClick={() => setIsCreatingNote(false)}
                    style={{
                      padding: '8px 16px',
                      borderRadius: 8,
                      border: '1px solid var(--color-border)',
                      background: 'transparent',
                      color: 'var(--color-text-muted)',
                      cursor: 'pointer'
                    }}
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleCreateNote}
                    disabled={!noteTitle.trim() || !noteContent.trim()}
                    style={{
                      padding: '8px 20px',
                      borderRadius: 8,
                      border: 'none',
                      background: 'var(--color-accent)',
                      color: '#fff',
                      fontWeight: 600,
                      cursor: !noteTitle.trim() || !noteContent.trim() ? 'not-allowed' : 'pointer'
                    }}
                  >
                    Save & Index Note
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
