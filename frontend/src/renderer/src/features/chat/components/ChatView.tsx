/* ═══════════════════════════════════════════════════════════
   ChatView Component — Main chat interface with Quick Action Chips & Export
   ═══════════════════════════════════════════════════════════ */

import { useRef, useEffect, useCallback, useState } from 'react'
import MessageBubble from './MessageBubble'
import InputComposer from './InputComposer'
import ThinkingIndicator from './ThinkingIndicator'
import type { Message, ApprovalRequest } from '@/shared/types'
import logoImg from '@/assets/logo.png'

interface ChatViewProps {
  messages: Message[]
  isStreaming: boolean
  isThinking: boolean
  onSendMessage: (content: string) => void
  onApprovalResponse: (id: string, approved: boolean, reason?: string) => void
  pendingApproval: ApprovalRequest | null
}

export default function ChatView({
  messages,
  isStreaming,
  isThinking,
  onSendMessage,
  onApprovalResponse,
  pendingApproval
}: ChatViewProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [copiedExport, setCopiedExport] = useState(false)

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, isThinking, isStreaming, scrollToBottom])

  // Export conversation as Markdown
  const handleExportMarkdown = () => {
    if (messages.length === 0) return
    let md = `# Chaitanya Karya Conversation Export\n*Exported on: ${new Date().toLocaleString()}*\n\n---\n\n`
    messages.forEach((m) => {
      const speaker = m.role === 'user' ? '👤 **You**' : '🤖 **Chaitanya Karya**'
      const time = new Date(m.created_at).toLocaleTimeString()
      md += `### ${speaker} *(${time})*\n\n${m.content}\n\n`
      if (m.tool_calls && m.tool_calls.length > 0) {
        md += `*Tools executed: ${m.tool_calls.map((t) => t.tool_name).join(', ')}*\n\n`
      }
      md += `---\n\n`
    })

    const blob = new Blob([md], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `chaitanya-karya-chat-${Date.now()}.md`
    a.click()
    URL.revokeObjectURL(url)

    setCopiedExport(true)
    setTimeout(() => setCopiedExport(false), 2000)
  }

  return (
    <div
      style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        position: 'relative',
        overflow: 'hidden'
      }}
    >
      {/* Top action header for Export */}
      {messages.length > 0 && (
        <div
          style={{
            display: 'flex',
            justifyContent: 'flex-end',
            padding: '8px 32px 0',
            background: 'transparent'
          }}
        >
          <button
            onClick={handleExportMarkdown}
            title="Export conversation to Markdown (.md)"
            style={{
              background: 'var(--color-bg-secondary)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              padding: '4px 10px',
              fontSize: '0.75rem',
              color: 'var(--color-text-muted)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              transition: 'all 0.2s'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = 'var(--color-text-primary)'
              e.currentTarget.style.borderColor = 'var(--color-border-focus)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = 'var(--color-text-muted)'
              e.currentTarget.style.borderColor = 'var(--color-border)'
            }}
          >
            <span>{copiedExport ? '✅ Exported!' : '📥 Export Chat (.md)'}</span>
          </button>
        </div>
      )}

      {/* Messages area */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '16px 32px 16px',
          display: 'flex',
          flexDirection: 'column',
          gap: 16
        }}
      >
        {messages.length === 0 ? (
          <WelcomeScreen onSuggestionClick={onSendMessage} />
        ) : (
          messages.map((message) => (
            <MessageBubble
              key={message.id}
              message={message}
              onApprovalResponse={onApprovalResponse}
            />
          ))
        )}

        {isThinking && <ThinkingIndicator />}

        <div ref={messagesEndRef} />
      </div>

      {/* Composer Container */}
      <div
        style={{
          padding: '0 32px 24px',
          background: 'linear-gradient(to top, var(--color-bg-primary) 80%, transparent)'
        }}
      >
        <InputComposer
          onSubmit={onSendMessage}
          disabled={isStreaming || !!pendingApproval}
          placeholder={
            pendingApproval
              ? 'Waiting for your approval decision...'
              : isStreaming
                ? 'Chaitanya Karya is thinking...'
                : 'Ask Chaitanya Karya anything...'
          }
        />
      </div>
    </div>
  )
}

/* ── Welcome Screen with Categorized Quick Action Chips ── */

function WelcomeScreen({ onSuggestionClick }: { onSuggestionClick: (text: string) => void }) {
  const suggestions = [
    {
      icon: '📊',
      title: 'Check live CPU & RAM metrics',
      desc: 'Real-time CPU load, memory usage, disk & battery'
    },
    {
      icon: '🔍',
      title: 'Search the web for latest AI news',
      desc: 'Live instant search with web facts and links'
    },
    {
      icon: '🌅',
      title: 'Prepare me for tomorrow',
      desc: 'Check calendar, emails & create executive briefing'
    },
    {
      icon: '🌦️',
      title: 'What is the weather today?',
      desc: 'Get real-time temperature, wind & forecasts'
    },
    {
      icon: '📸',
      title: 'Take a screenshot',
      desc: 'Capture active screen & save to Documents'
    },
    {
      icon: '🌐',
      title: 'Check network status & ping',
      desc: 'Verify internet latency and local IP'
    },
    {
      icon: '🎵',
      title: 'Toggle media playback',
      desc: 'Play/pause music or adjust system audio'
    },
    {
      icon: '📋',
      title: 'Read what is on my clipboard',
      desc: 'Inspect and extract text from system clipboard'
    }
  ]

  return (
    <div
      style={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px 24px',
        gap: 20
      }}
    >
      {/* Logo */}
      <div
        style={{
          width: 72,
          height: 72,
          borderRadius: 'var(--radius-xl)',
          background: 'var(--color-bg-secondary)',
          border: '1px solid var(--color-border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: 'var(--shadow-glow-lg)',
          animation: 'var(--animate-scale-in)',
          padding: 10
        }}
      >
        <img
          src={logoImg}
          alt="Chaitanya Karya Logo"
          style={{ width: '100%', height: '100%', objectFit: 'contain' }}
        />
      </div>

      {/* Heading */}
      <div style={{ textAlign: 'center', animation: 'var(--animate-slide-up)' }}>
        <h1
          style={{
            fontSize: '1.5rem',
            fontWeight: 700,
            color: 'var(--color-text-primary)',
            letterSpacing: '-0.02em',
            marginBottom: 6
          }}
        >
          Welcome to Chaitanya Karya
        </h1>
        <p
          style={{
            fontSize: '0.875rem',
            color: 'var(--color-text-muted)',
            maxWidth: 460,
            lineHeight: 1.5
          }}
        >
          Your permission-aware AI executive assistant. Press <kbd style={{ background: 'rgba(255,255,255,0.08)', padding: '2px 5px', borderRadius: '4px', border: '1px solid rgba(255,255,255,0.1)' }}>Ctrl+Shift+Space</kbd> anytime from anywhere.
        </p>
      </div>

      {/* Suggestion cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: 10,
          maxWidth: 620,
          width: '100%',
          animation: 'var(--animate-slide-up)'
        }}
      >
        {suggestions.map((s) => (
          <button
            key={s.title}
            onClick={() => onSuggestionClick(s.title)}
            style={{
              padding: '12px 14px',
              background: 'var(--color-bg-secondary)',
              border: '1px solid var(--color-border-subtle)',
              borderRadius: 'var(--radius-lg)',
              cursor: 'pointer',
              textAlign: 'left',
              transition: 'all 0.2s',
              fontFamily: 'var(--font-sans)',
              display: 'flex',
              alignItems: 'flex-start',
              gap: 10
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'var(--color-bg-tertiary)'
              e.currentTarget.style.borderColor = 'var(--color-border)'
              e.currentTarget.style.transform = 'translateY(-2px)'
              e.currentTarget.style.boxShadow = 'var(--shadow-md)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'var(--color-bg-secondary)'
              e.currentTarget.style.borderColor = 'var(--color-border-subtle)'
              e.currentTarget.style.transform = 'translateY(0)'
              e.currentTarget.style.boxShadow = 'none'
            }}
          >
            <span style={{ fontSize: '1.25rem', lineHeight: 1 }}>
              {s.icon}
            </span>
            <div>
              <span
                style={{
                  fontSize: '0.8125rem',
                  fontWeight: 600,
                  color: 'var(--color-text-primary)',
                  display: 'block',
                  marginBottom: 2
                }}
              >
                {s.title}
              </span>
              <span
                style={{
                  fontSize: '0.71875rem',
                  color: 'var(--color-text-muted)',
                  lineHeight: 1.3,
                  display: 'block'
                }}
              >
                {s.desc}
              </span>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}

