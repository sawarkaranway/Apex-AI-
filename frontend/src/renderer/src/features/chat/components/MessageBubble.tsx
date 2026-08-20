/* ═══════════════════════════════════════════════════════════
   MessageBubble Component — Individual message display with TTS
   ═══════════════════════════════════════════════════════════ */

import { useState, useEffect } from 'react'
import Avatar from '@/shared/components/Avatar'
import ToolCallCard from './ToolCallCard'
import ApprovalModal from '@/features/approval/components/ApprovalModal'
import type { Message } from '@/shared/types'

interface MessageBubbleProps {
  message: Message
  onApprovalResponse: (id: string, approved: boolean, reason?: string) => void
}

export default function MessageBubble({ message, onApprovalResponse }: MessageBubbleProps) {
  const isUser = message.role === 'user'
  const isStreaming = message.status === 'streaming'
  const [isSpeaking, setIsSpeaking] = useState(false)

  // Handle Speech Synthesis
  const toggleSpeech = () => {
    if (!('speechSynthesis' in window)) {
      alert('Text-to-speech is not supported in this environment.')
      return
    }

    if (isSpeaking) {
      window.speechSynthesis.cancel()
      setIsSpeaking(false)
      return
    }

    window.speechSynthesis.cancel() // Stop any previous speech
    const cleanText = message.content.replace(/```[\s\S]*?```/g, 'Code block omitted.')
    const utterance = new SpeechSynthesisUtterance(cleanText)
    utterance.rate = 1.0
    utterance.pitch = 1.0

    utterance.onend = () => setIsSpeaking(false)
    utterance.onerror = () => setIsSpeaking(false)

    window.speechSynthesis.speak(utterance)
    setIsSpeaking(true)
  }

  // Cleanup speech on unmount
  useEffect(() => {
    return () => {
      if (isSpeaking) {
        window.speechSynthesis.cancel()
      }
    }
  }, [isSpeaking])

  return (
    <div
      style={{
        display: 'flex',
        gap: 12,
        padding: '16px 0',
        animation: 'var(--animate-fade-in)'
      }}
    >
      {/* Avatar */}
      <div style={{ flexShrink: 0, paddingTop: 2 }}>
        <Avatar
          isAssistant={!isUser}
          name={isUser ? 'Arman Tiwari' : undefined}
          size={30}
        />
      </div>

      {/* Content */}
      <div style={{ flex: 1, minWidth: 0 }}>
        {/* Role label & Speak button */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: 6
          }}
        >
          <span
            style={{
              fontSize: '0.8125rem',
              fontWeight: 600,
              color: isUser ? 'var(--color-text-primary)' : 'var(--color-accent)'
            }}
          >
            {isUser ? 'You' : 'Chaitanya Karya'}
          </span>

          {!isUser && message.content && (
            <button
              onClick={toggleSpeech}
              title={isSpeaking ? 'Stop speaking' : 'Read aloud (Text-to-Speech)'}
              style={{
                background: isSpeaking ? 'rgba(139, 92, 246, 0.2)' : 'transparent',
                border: 'none',
                borderRadius: '6px',
                padding: '2px 6px',
                cursor: 'pointer',
                color: isSpeaking ? 'var(--color-accent)' : 'var(--color-text-muted)',
                fontSize: '0.75rem',
                display: 'flex',
                alignItems: 'center',
                gap: 4,
                transition: 'all 0.2s'
              }}
            >
              <span>{isSpeaking ? '⏹ Stop' : '🔊 Listen'}</span>
            </button>
          )}
        </div>

        {/* Message content */}
        <div
          className="markdown-content"
          style={{
            fontSize: '0.875rem',
            lineHeight: 1.7,
            color: 'var(--color-text-secondary)',
            wordBreak: 'break-word'
          }}
        >
          {renderContent(message.content)}
          {isStreaming && (
            <span
              style={{
                display: 'inline-block',
                width: 2,
                height: '1em',
                background: 'var(--color-accent)',
                marginLeft: 2,
                animation: 'cursor-blink 1s step-end infinite',
                verticalAlign: 'text-bottom'
              }}
            />
          )}
        </div>

        {/* Tool calls */}
        {message.tool_calls && message.tool_calls.length > 0 && (
          <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
            {message.tool_calls.map((tc) => (
              <ToolCallCard key={tc.id} toolCall={tc} />
            ))}
          </div>
        )}

        {/* Approval request */}
        {message.approval_request && message.approval_request.status === 'pending' && (
          <div style={{ marginTop: 12 }}>
            <ApprovalModal
              request={message.approval_request}
              onRespond={onApprovalResponse}
              inline
            />
          </div>
        )}

        {/* Timestamp */}
        <div
          style={{
            fontSize: '0.6875rem',
            color: 'var(--color-text-muted)',
            marginTop: 8,
            opacity: 0.6
          }}
        >
          {new Date(message.created_at).toLocaleTimeString('en-US', {
            hour: 'numeric',
            minute: '2-digit',
            hour12: true
          })}
        </div>
      </div>
    </div>
  )
}

/* ── Simple markdown-like rendering ── */

function renderContent(content: string): React.ReactNode {
  if (!content) return null

  // Split by double newlines for paragraphs
  const paragraphs = content.split('\n\n')

  return paragraphs.map((para, i) => {
    // Check for code blocks
    if (para.startsWith('```')) {
      const lines = para.split('\n')
      const lang = lines[0].replace('```', '').trim()
      const code = lines.slice(1, lines.length - 1).join('\n')
      return (
        <pre key={i} style={{ position: 'relative' }}>
          {lang && (
            <span
              style={{
                position: 'absolute',
                top: 8,
                right: 12,
                fontSize: '0.6875rem',
                color: 'var(--color-text-muted)',
                textTransform: 'uppercase'
              }}
            >
              {lang}
            </span>
          )}
          <code>{code}</code>
        </pre>
      )
    }

    // Check for bullet lists
    if (para.match(/^[-*•]\s/m)) {
      const items = para.split('\n').filter((l) => l.trim())
      return (
        <ul key={i}>
          {items.map((item, j) => (
            <li key={j}>{item.replace(/^[-*•]\s+/, '')}</li>
          ))}
        </ul>
      )
    }

    // Regular paragraph with inline formatting
    const lines = para.split('\n')
    return (
      <p key={i}>
        {lines.map((line, j) => (
          <span key={j}>
            {j > 0 && <br />}
            {renderInline(line)}
          </span>
        ))}
      </p>
    )
  })
}

function renderInline(text: string): React.ReactNode {
  // Bold
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g)
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={i} style={{ color: 'var(--color-text-primary)', fontWeight: 600 }}>
          {part.slice(2, -2)}
        </strong>
      )
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return <code key={i}>{part.slice(1, -1)}</code>
    }
    return part
  })
}
