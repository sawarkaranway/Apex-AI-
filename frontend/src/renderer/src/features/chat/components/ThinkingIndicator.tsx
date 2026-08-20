/* ═══════════════════════════════════════════════════════════
   ThinkingIndicator Component
   ═══════════════════════════════════════════════════════════ */

import Avatar from '@/shared/components/Avatar'

export default function ThinkingIndicator() {
  return (
    <div
      style={{
        display: 'flex',
        gap: 12,
        padding: '16px 0',
        animation: 'var(--animate-fade-in)'
      }}
    >
      <div style={{ flexShrink: 0, paddingTop: 2 }}>
        <Avatar isAssistant size={30} />
      </div>

      <div>
        <div
          style={{
            fontSize: '0.8125rem',
            fontWeight: 600,
            color: 'var(--color-accent)',
            marginBottom: 8
          }}
        >
          Chaitanya Karya
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 4, height: 24 }}>
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              style={{
                width: 6,
                height: 6,
                borderRadius: '50%',
                background: 'var(--color-accent)',
                animation: 'typing-dot 1.4s ease-in-out infinite',
                animationDelay: `${i * 0.2}s`
              }}
            />
          ))}
          <span
            style={{
              fontSize: '0.8125rem',
              color: 'var(--color-text-muted)',
              marginLeft: 8,
              fontStyle: 'italic'
            }}
          >
            Thinking...
          </span>
        </div>
      </div>
    </div>
  )
}
