/* ═══════════════════════════════════════════════════════════
   ToolCallCard Component — Tool execution display
   ═══════════════════════════════════════════════════════════ */

import { useState } from 'react'
import Badge from '@/shared/components/Badge'
import { getToolIcon } from '@/shared/lib/constants'
import type { ToolCall } from '@/shared/types'

interface ToolCallCardProps {
  toolCall: ToolCall
}

const statusConfig = {
  pending: { variant: 'default' as const, label: 'Pending' },
  running: { variant: 'info' as const, label: 'Running' },
  success: { variant: 'success' as const, label: 'Complete' },
  error: { variant: 'danger' as const, label: 'Error' },
  approval_required: { variant: 'warning' as const, label: 'Needs Approval' }
}

export default function ToolCallCard({ toolCall }: ToolCallCardProps) {
  const [expanded, setExpanded] = useState(false)
  const config = statusConfig[toolCall.status]
  const icon = getToolIcon(toolCall.tool_name)

  return (
    <div
      style={{
        background: 'var(--color-bg-secondary)',
        border: '1px solid var(--color-border-subtle)',
        borderRadius: 'var(--radius-lg)',
        overflow: 'hidden',
        animation: 'var(--animate-slide-up)'
      }}
    >
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        style={{
          width: '100%',
          padding: '10px 14px',
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          fontFamily: 'var(--font-sans)',
          transition: 'background 0.15s'
        }}
        onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--color-bg-tertiary)')}
        onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
      >
        {/* Tool icon */}
        <span style={{ fontSize: '1rem' }}>{icon}</span>

        {/* Tool name */}
        <span
          style={{
            fontSize: '0.8125rem',
            fontWeight: 500,
            color: 'var(--color-text-primary)',
            flex: 1,
            textAlign: 'left'
          }}
        >
          {toolCall.tool_display_name}
        </span>

        {/* Status badge */}
        <Badge variant={config.variant} size="sm" dot>
          {config.label}
        </Badge>

        {/* Spinner for running */}
        {toolCall.status === 'running' && (
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            style={{ animation: 'spin 0.8s linear infinite' }}
          >
            <path
              d="M12 2a10 10 0 0 1 10 10"
              stroke="var(--color-accent)"
              strokeWidth="3"
              strokeLinecap="round"
            />
          </svg>
        )}

        {/* Chevron */}
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="var(--color-text-muted)"
          strokeWidth="2"
          strokeLinecap="round"
          style={{
            transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
            transition: 'transform 0.2s'
          }}
        >
          <path d="M6 9l6 6 6-6" />
        </svg>
      </button>

      {/* Expanded content */}
      {expanded && (
        <div
          style={{
            padding: '0 14px 14px',
            borderTop: '1px solid var(--color-border-subtle)',
            animation: 'var(--animate-fade-in)'
          }}
        >
          {/* Arguments */}
          {Object.keys(toolCall.arguments).length > 0 && (
            <div style={{ marginTop: 12 }}>
              <div
                style={{
                  fontSize: '0.6875rem',
                  fontWeight: 600,
                  color: 'var(--color-text-muted)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  marginBottom: 6
                }}
              >
                Arguments
              </div>
              <pre
                style={{
                  background: 'var(--color-bg-primary)',
                  border: '1px solid var(--color-border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  padding: '10px 12px',
                  fontSize: '0.75rem',
                  fontFamily: 'var(--font-mono)',
                  color: 'var(--color-text-secondary)',
                  overflowX: 'auto',
                  margin: 0,
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-all'
                }}
              >
                {JSON.stringify(toolCall.arguments, null, 2)}
              </pre>
            </div>
          )}

          {/* Result */}
          {toolCall.result && (
            <div style={{ marginTop: 12 }}>
              <div
                style={{
                  fontSize: '0.6875rem',
                  fontWeight: 600,
                  color: 'var(--color-text-muted)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  marginBottom: 6
                }}
              >
                Result
              </div>
              <div
                style={{
                  background: 'var(--color-bg-primary)',
                  border: '1px solid var(--color-border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  padding: '12px 14px',
                  fontSize: '0.8125rem',
                  color: 'var(--color-text-primary)',
                  lineHeight: 1.6,
                  whiteSpace: 'pre-wrap',
                  fontFamily: 'var(--font-sans)'
                }}
              >
                {toolCall.result}
                {(() => {
                  const urlMatch = toolCall.result.match(/https?:\/\/[^\s'"]+/);
                  if (urlMatch) {
                    return (
                      <div style={{ marginTop: 10 }}>
                        <a
                          href={urlMatch[0]}
                          target="_blank"
                          rel="noreferrer"
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: 6,
                            background: 'rgba(56, 189, 248, 0.15)',
                            color: '#38BDF8',
                            padding: '6px 12px',
                            borderRadius: '6px',
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            textDecoration: 'none',
                            border: '1px solid rgba(56, 189, 248, 0.3)',
                            cursor: 'pointer'
                          }}
                        >
                          ▶ Open in Browser ↗
                        </a>
                      </div>
                    );
                  }
                  return null;
                })()}
              </div>
            </div>
          )}

          {/* Error */}
          {toolCall.error && (
            <div style={{ marginTop: 12 }}>
              <div
                style={{
                  background: 'var(--color-danger-muted)',
                  border: '1px solid oklch(0.45 0.12 25)',
                  borderRadius: 'var(--radius-md)',
                  padding: '10px 12px',
                  fontSize: '0.8125rem',
                  color: 'var(--color-danger)',
                  lineHeight: 1.5
                }}
              >
                ⚠️ {toolCall.error}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
