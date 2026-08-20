/* ═══════════════════════════════════════════════════════════
   Avatar Component — Aegis AI Design System
   ═══════════════════════════════════════════════════════════ */

interface AvatarProps {
  src?: string
  name?: string
  size?: number
  isAssistant?: boolean
}

function getInitials(name: string): string {
  return name
    .split(' ')
    .map((w) => w[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()
}

export default function Avatar({ src, name, size = 32, isAssistant }: AvatarProps) {
  if (isAssistant) {
    return (
      <div
        style={{
          width: size,
          height: size,
          borderRadius: 'var(--radius-lg)',
          background: 'linear-gradient(135deg, oklch(0.50 0.18 250), oklch(0.65 0.20 280))',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          boxShadow: 'var(--shadow-glow)'
        }}
      >
        <svg width={size * 0.55} height={size * 0.55} viewBox="0 0 24 24" fill="none">
          <path
            d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"
            fill="white"
            opacity={0.9}
          />
        </svg>
      </div>
    )
  }

  if (src) {
    return (
      <img
        src={src}
        alt={name || 'User'}
        style={{
          width: size,
          height: size,
          borderRadius: 'var(--radius-lg)',
          objectFit: 'cover',
          flexShrink: 0
        }}
      />
    )
  }

  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: 'var(--radius-lg)',
        background: 'var(--color-bg-tertiary)',
        border: '1px solid var(--color-border-subtle)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0,
        fontSize: size * 0.38,
        fontWeight: 600,
        color: 'var(--color-text-secondary)'
      }}
    >
      {name ? getInitials(name) : 'U'}
    </div>
  )
}
