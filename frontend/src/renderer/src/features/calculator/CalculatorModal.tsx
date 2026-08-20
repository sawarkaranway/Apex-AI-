/* ═══════════════════════════════════════════════════════════
   Scientific Calculator Component — Chaitanya Karya
   Features:
   - Natural Language Mathematical Query Parser
   - Interactive Scientific Keypad (Trig, Calculus, Matrix, Log, Powers)
   - Exact Symbolic Answer vs Approximate Numerical Display
   - Step-by-Step Solution Breakdown & Formula Used
   - Independent Verification Indicator
   - User-Isolated Calculation History & 1-Click Reuse
   ═══════════════════════════════════════════════════════════ */

import React, { useState, useEffect } from 'react'
import api from '@/shared/lib/api'

interface MathResult {
  status: 'success' | 'error'
  operation?: string
  exact_answer?: string
  approximate_answer?: string
  formula_used?: string
  steps?: string[]
  units?: string | null
  error_type?: string
  message?: string
  suggestion?: string
  verification?: {
    performed: boolean
    passed: boolean
    details?: string
  }
}

interface HistoryItem {
  id: string
  query: string
  operation: string
  exact_answer: string
  approximate_answer: string
  formula_used: string
  steps: string[]
  created_at: string
}

interface CalculatorModalProps {
  isOpen: boolean
  onClose: () => void
  onPasteToChat?: (text: string) => void
}

const EXAMPLE_QUERIES = [
  'What is 25% of 840?',
  'Solve 2x^2 + 5x - 3 = 0',
  'Integrate x^2 + 3x from 0 to 5',
  'Differentiate sin(x^2)',
  'Determinant of [[1, 2], [3, 4]]',
  'Compound interest on ₹50,000 at 8% for 5 years',
  'Solve 2x + y = 7, x - y = 1',
  'Convert 72 km/h to m/s',
  'mean of [10, 20, 30, 40, 50]',
  '8 choose 3'
]

export default function CalculatorModal({ isOpen, onClose, onPasteToChat }: CalculatorModalProps) {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<MathResult | null>(null)
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [activeTab, setActiveTab] = useState<'calc' | 'history'>('calc')
  const [copied, setCopied] = useState(false)

  // Fetch calculation history
  const loadHistory = async () => {
    try {
      const data = await api.get<{ history: HistoryItem[] }>('/calculator/history/')
      setHistory(data.history || [])
    } catch (err) {
      console.warn('Failed to load calculation history:', err)
    }
  }

  useEffect(() => {
    if (isOpen) {
      loadHistory()
    }
  }, [isOpen])

  if (!isOpen) return null

  const handleCalculate = async (customQuery?: string) => {
    const q = (customQuery || query).trim()
    if (!q) return

    setLoading(true)
    setResult(null)

    try {
      const res = await api.post<MathResult>('/calculator/evaluate/', { query: q })
      setResult(res)
      loadHistory()
    } catch (err: any) {
      setResult({
        status: 'error',
        error_type: 'network_error',
        message: err.message || 'Failed to connect to math computation engine.'
      })
    } finally {
      setLoading(false)
    }
  }

  const handleKeypadPress = (val: string) => {
    setQuery((prev) => prev + val)
  }

  const handleClear = () => {
    setQuery('')
    setResult(null)
  }

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleDeleteHistoryItem = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await api.delete(`/calculator/history/${id}/`)
      setHistory((prev) => prev.filter((h) => h.id !== id))
    } catch (err) {
      console.error(err)
    }
  }

  const handleClearHistory = async () => {
    try {
      await api.delete('/calculator/history/')
      setHistory([])
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
          maxWidth: 820,
          maxHeight: '90vh',
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
                background: 'linear-gradient(135deg, #38BDF8 0%, #6366F1 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.2rem',
                color: '#fff'
              }}
            >
              ∑
            </div>
            <div>
              <h2 style={{ fontSize: '1.1rem', fontWeight: 700, margin: 0, color: 'var(--color-text-primary)' }}>
                Scientific Calculator & Math Engine
              </h2>
              <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                Deterministic Symbolic & Numerical Engine (SymPy + AST Sandboxed)
              </span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {/* Tabs */}
            <div style={{ display: 'flex', background: 'var(--color-bg-primary)', borderRadius: 8, padding: 3 }}>
              <button
                onClick={() => setActiveTab('calc')}
                style={{
                  padding: '5px 12px',
                  borderRadius: 6,
                  border: 'none',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  background: activeTab === 'calc' ? 'var(--color-accent)' : 'transparent',
                  color: activeTab === 'calc' ? '#fff' : 'var(--color-text-secondary)'
                }}
              >
                Calculator
              </button>
              <button
                onClick={() => setActiveTab('history')}
                style={{
                  padding: '5px 12px',
                  borderRadius: 6,
                  border: 'none',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  background: activeTab === 'history' ? 'var(--color-accent)' : 'transparent',
                  color: activeTab === 'history' ? '#fff' : 'var(--color-text-secondary)'
                }}
              >
                History ({history.length})
              </button>
            </div>

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

        {/* Body */}
        <div style={{ flex: 1, overflowY: 'auto', padding: 24, display: 'flex', flexDirection: 'column', gap: 20 }}>
          {activeTab === 'calc' ? (
            <>
              {/* Natural Language Input Bar */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <div style={{ display: 'flex', gap: 8 }}>
                  <input
                    type="text"
                    placeholder="Enter mathematical problem or natural language query (e.g., Solve 2x² + 5x - 3 = 0)"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleCalculate()}
                    style={{
                      flex: 1,
                      padding: '12px 16px',
                      borderRadius: 10,
                      background: 'var(--color-bg-primary)',
                      border: '1px solid var(--color-border)',
                      color: 'var(--color-text-primary)',
                      fontSize: '0.95rem',
                      outline: 'none',
                      fontFamily: 'monospace'
                    }}
                  />
                  <button
                    onClick={() => handleCalculate()}
                    disabled={loading || !query.trim()}
                    style={{
                      padding: '0 24px',
                      borderRadius: 10,
                      border: 'none',
                      background: 'var(--color-accent-gradient, linear-gradient(135deg, #38BDF8 0%, #6366F1 100%))',
                      color: '#fff',
                      fontWeight: 600,
                      cursor: loading || !query.trim() ? 'not-allowed' : 'pointer',
                      opacity: loading || !query.trim() ? 0.6 : 1,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8
                    }}
                  >
                    {loading ? 'Evaluating...' : 'Solve ↵'}
                  </button>
                  {query && (
                    <button
                      onClick={handleClear}
                      title="Clear input"
                      style={{
                        padding: '0 16px',
                        borderRadius: 10,
                        border: '1px solid var(--color-border)',
                        background: 'transparent',
                        color: 'var(--color-text-muted)',
                        cursor: 'pointer'
                      }}
                    >
                      Clear
                    </button>
                  )}
                </div>

                {/* Example Query Pills */}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {EXAMPLE_QUERIES.map((ex, i) => (
                    <span
                      key={i}
                      onClick={() => {
                        setQuery(ex)
                        handleCalculate(ex)
                      }}
                      style={{
                        fontSize: '0.72rem',
                        padding: '4px 10px',
                        borderRadius: 20,
                        background: 'var(--color-bg-tertiary)',
                        border: '1px solid var(--color-border)',
                        color: 'var(--color-text-secondary)',
                        cursor: 'pointer',
                        transition: 'all 0.15s'
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--color-accent)')}
                      onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--color-border)')}
                    >
                      {ex}
                    </span>
                  ))}
                </div>
              </div>

              {/* Result Area */}
              {result && (
                <div
                  style={{
                    padding: 16,
                    borderRadius: 12,
                    background: result.status === 'success' ? 'rgba(56, 189, 248, 0.08)' : 'rgba(239, 68, 68, 0.08)',
                    border: `1px solid ${result.status === 'success' ? 'rgba(56, 189, 248, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 12
                  }}
                >
                  {result.status === 'success' ? (
                    <>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                            <span style={{ fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase', color: '#38BDF8', letterSpacing: '0.05em' }}>
                              {result.operation?.replace('_', ' ')}
                            </span>
                            {result.formula_used && (
                              <span style={{ fontSize: '0.75rem', padding: '2px 8px', borderRadius: 4, background: 'rgba(99, 102, 241, 0.2)', color: '#818CF8' }}>
                                {result.formula_used}
                              </span>
                            )}
                          </div>
                          <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--color-text-primary)', fontFamily: 'monospace' }}>
                            {result.exact_answer}
                          </div>
                          {result.approximate_answer && result.approximate_answer !== result.exact_answer && (
                            <div style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginTop: 2 }}>
                              Approximate Decimal: <span style={{ fontFamily: 'monospace', fontWeight: 600 }}>{result.approximate_answer}</span>
                            </div>
                          )}
                        </div>

                        <div style={{ display: 'flex', gap: 6 }}>
                          <button
                            onClick={() => handleCopy(result.exact_answer || '')}
                            style={{
                              padding: '6px 12px',
                              borderRadius: 6,
                              border: '1px solid var(--color-border)',
                              background: 'var(--color-bg-primary)',
                              color: copied ? '#10B981' : 'var(--color-text-secondary)',
                              fontSize: '0.75rem',
                              cursor: 'pointer',
                              display: 'flex',
                              alignItems: 'center',
                              gap: 4
                            }}
                          >
                            {copied ? '✓ Copied' : 'Copy'}
                          </button>
                          {onPasteToChat && (
                            <button
                              onClick={() => {
                                onPasteToChat(`Mathematical Result: ${result.exact_answer} (${result.formula_used || ''})`)
                                onClose()
                              }}
                              style={{
                                padding: '6px 12px',
                                borderRadius: 6,
                                border: 'none',
                                background: 'var(--color-accent)',
                                color: '#fff',
                                fontSize: '0.75rem',
                                fontWeight: 600,
                                cursor: 'pointer'
                              }}
                            >
                              Insert in Chat
                            </button>
                          )}
                        </div>
                      </div>

                      {/* Step-by-Step Breakdown */}
                      {result.steps && result.steps.length > 0 && (
                        <div style={{ borderTop: '1px solid rgba(255, 255, 255, 0.08)', paddingTop: 12 }}>
                          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
                            Step-by-Step Solution:
                          </span>
                          <div style={{ marginTop: 6, display: 'flex', flexDirection: 'column', gap: 4 }}>
                            {result.steps.map((step, idx) => (
                              <div key={idx} style={{ fontSize: '0.8125rem', color: 'var(--color-text-primary)', display: 'flex', gap: 6 }}>
                                <span style={{ color: '#38BDF8' }}>•</span>
                                <span>{step}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Verification Badge */}
                      {result.verification?.performed && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.75rem', color: result.verification.passed ? '#10B981' : '#F59E0B' }}>
                          <span>{result.verification.passed ? '🛡️ Verification Passed:' : '⚠️ Verification Note:'}</span>
                          <span>{result.verification.details}</span>
                        </div>
                      )}
                    </>
                  ) : (
                    <div>
                      <div style={{ fontWeight: 600, color: '#EF4444', fontSize: '0.9rem', marginBottom: 4 }}>
                        ❌ Error [{result.error_type || 'math_error'}]: {result.message}
                      </div>
                      {result.suggestion && (
                        <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                          💡 Suggestion: {result.suggestion}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Scientific Keypad */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(6, 1fr)',
                  gap: 8,
                  background: 'var(--color-bg-primary)',
                  padding: 16,
                  borderRadius: 12,
                  border: '1px solid var(--color-border)'
                }}
              >
                {[
                  'sin(', 'cos(', 'tan(', 'log(', 'ln(', 'sqrt(',
                  'diff(', 'integrate(', 'limit(', 'det(', 'inv(', '^',
                  '(', ')', 'pi', 'E', 'x', 'y',
                  '7', '8', '9', '/', ' mean(', '%',
                  '4', '5', '6', '*', 'stdev(', 'C(',
                  '1', '2', '3', '-', 'factorial(', '=',
                  '0', '.', ',', '+', '[[', ']]'
                ].map((keyVal, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleKeypadPress(keyVal)}
                    style={{
                      padding: '10px 0',
                      borderRadius: 8,
                      border: '1px solid var(--color-border)',
                      background: ['/', '*', '-', '+', '='].includes(keyVal) ? 'rgba(56, 189, 248, 0.15)' : 'var(--color-bg-secondary)',
                      color: ['/', '*', '-', '+', '='].includes(keyVal) ? '#38BDF8' : 'var(--color-text-primary)',
                      fontSize: '0.85rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      transition: 'background 0.15s'
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--color-bg-tertiary)')}
                    onMouseLeave={(e) => (e.currentTarget.style.background = ['/', '*', '-', '+', '='].includes(keyVal) ? 'rgba(56, 189, 248, 0.15)' : 'var(--color-bg-secondary)')}
                  >
                    {keyVal}
                  </button>
                ))}
              </div>
            </>
          ) : (
            /* History Tab */
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-text-secondary)' }}>
                  Previous Calculations ({history.length})
                </span>
                {history.length > 0 && (
                  <button
                    onClick={handleClearHistory}
                    style={{
                      padding: '4px 10px',
                      borderRadius: 6,
                      border: '1px solid var(--color-border)',
                      background: 'transparent',
                      color: '#EF4444',
                      fontSize: '0.75rem',
                      cursor: 'pointer'
                    }}
                  >
                    Clear All History
                  </button>
                )}
              </div>

              {history.length === 0 ? (
                <div style={{ textAlign: 'center', padding: 40, color: 'var(--color-text-muted)' }}>
                  No previous calculations found.
                </div>
              ) : (
                history.map((item) => (
                  <div
                    key={item.id}
                    onClick={() => {
                      setQuery(item.query)
                      setActiveTab('calc')
                      handleCalculate(item.query)
                    }}
                    style={{
                      padding: 14,
                      borderRadius: 10,
                      background: 'var(--color-bg-primary)',
                      border: '1px solid var(--color-border)',
                      cursor: 'pointer',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center'
                    }}
                  >
                    <div>
                      <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-text-primary)', fontFamily: 'monospace' }}>
                        {item.query}
                      </div>
                      <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#38BDF8', marginTop: 2 }}>
                        = {item.exact_answer}
                      </div>
                      {item.formula_used && (
                        <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: 2 }}>
                          {item.formula_used}
                        </div>
                      )}
                    </div>

                    <button
                      onClick={(e) => handleDeleteHistoryItem(item.id, e)}
                      title="Delete calculation"
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: 'var(--color-text-muted)',
                        cursor: 'pointer',
                        padding: 6
                      }}
                    >
                      ✕
                    </button>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
