/* ═══════════════════════════════════════════════════════════
   ConversationList Component
   ═══════════════════════════════════════════════════════════ */

import type { Conversation } from '@/shared/types'

interface ConversationListProps {
  conversations: Conversation[]
  activeId: string | null
  onSelect: (id: string) => void
}

function timeAgo(dateString: string): string {
  const now = new Date()
  const date = new Date(dateString)
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000)

  if (seconds < 60) return 'just now'
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

export default function ConversationList({
  conversations,
  activeId,
  onSelect
}: ConversationListProps) {
  if (conversations.length === 0) {
    return (
      <div
        style={{
          padding: '32px 16px',
          textAlign: 'center',
          color: 'var(--color-text-muted)',
          fontSize: '0.8125rem'
        }}
      >
        <svg
          width="32"
          height="32"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          style={{ margin: '0 auto 8px', opacity: 0.4 }}
        >
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        </svg>
        <p>No conversations yet</p>
        <p style={{ fontSize: '0.75rem', marginTop: 4, opacity: 0.7 }}>
          Start a new chat to begin
        </p>
      </div>
    )
  }

  // Group by date
  const today = new Date()
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)

  const groups: { label: string; items: Conversation[] }[] = []
  const todayItems: Conversation[] = []
  const yesterdayItems: Conversation[] = []
  const olderItems: Conversation[] = []

  conversations.forEach((c) => {
    const date = new Date(c.updated_at)
    if (date.toDateString() === today.toDateString()) {
      todayItems.push(c)
    } else if (date.toDateString() === yesterday.toDateString()) {
      yesterdayItems.push(c)
    } else {
      olderItems.push(c)
    }
  })

  if (todayItems.length) groups.push({ label: 'Today', items: todayItems })
  if (yesterdayItems.length) groups.push({ label: 'Yesterday', items: yesterdayItems })
  if (olderItems.length) groups.push({ label: 'Previous', items: olderItems })

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      {groups.map((group) => (
        <div key={group.label}>
          <div
            style={{
              padding: '8px 8px 4px',
              fontSize: '0.6875rem',
              fontWeight: 600,
              color: 'var(--color-text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em'
            }}
          >
            {group.label}
          </div>
          {group.items.map((conversation) => {
            const isActive = conversation.id === activeId
            return (
              <button
                key={conversation.id}
                onClick={() => onSelect(conversation.id)}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  background: isActive ? 'var(--color-bg-active)' : 'transparent',
                  border: 'none',
                  borderRadius: 'var(--radius-md)',
                  cursor: 'pointer',
                  textAlign: 'left',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 2,
                  transition: 'background 0.15s',
                  fontFamily: 'var(--font-sans)'
                }}
                onMouseEnter={(e) => {
                  if (!isActive) e.currentTarget.style.background = 'var(--color-bg-hover)'
                }}
                onMouseLeave={(e) => {
                  if (!isActive) e.currentTarget.style.background = 'transparent'
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}
                >
                  <span
                    style={{
                      fontSize: '0.8125rem',
                      fontWeight: isActive ? 600 : 400,
                      color: isActive
                        ? 'var(--color-text-primary)'
                        : 'var(--color-text-secondary)',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      flex: 1
                    }}
                  >
                    {conversation.title}
                  </span>
                  <span
                    style={{
                      fontSize: '0.6875rem',
                      color: 'var(--color-text-muted)',
                      flexShrink: 0,
                      marginLeft: 8
                    }}
                  >
                    {timeAgo(conversation.updated_at)}
                  </span>
                </div>
                {conversation.last_message_preview && (
                  <span
                    style={{
                      fontSize: '0.75rem',
                      color: 'var(--color-text-muted)',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}
                  >
                    {conversation.last_message_preview}
                  </span>
                )}
              </button>
            )
          })}
        </div>
      ))}
    </div>
  )
}
