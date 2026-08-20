/* ═══════════════════════════════════════════════════════════
   NewChatButton Component
   ═══════════════════════════════════════════════════════════ */

interface NewChatButtonProps {
  onClick: () => void
}

export default function NewChatButton({ onClick }: NewChatButtonProps) {
  return (
    <button
      onClick={onClick}
      id="new-chat-button"
      style={{
        width: '100%',
        padding: '10px 14px',
        background: 'var(--color-bg-tertiary)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-md)',
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        fontFamily: 'var(--font-sans)',
        fontSize: '0.8125rem',
        fontWeight: 500,
        color: 'var(--color-text-primary)',
        transition: 'all 0.2s'
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = 'var(--color-bg-hover)'
        e.currentTarget.style.borderColor = 'var(--color-accent-muted)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = 'var(--color-bg-tertiary)'
        e.currentTarget.style.borderColor = 'var(--color-border)'
      }}
    >
      <svg
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="var(--color-accent)"
        strokeWidth="2"
        strokeLinecap="round"
      >
        <path d="M12 5v14M5 12h14" />
      </svg>
      New Chat
    </button>
  )
}
