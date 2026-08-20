/* ═══════════════════════════════════════════════════════════
   Badge Component — Aegis AI Design System
   ═══════════════════════════════════════════════════════════ */

type BadgeVariant = 'default' | 'success' | 'warning' | 'danger' | 'critical' | 'info' | 'accent'

interface BadgeProps {
  children: React.ReactNode
  variant?: BadgeVariant
  size?: 'sm' | 'md'
  dot?: boolean
}

const variantMap: Record<BadgeVariant, { bg: string; text: string; dot: string }> = {
  default: {
    bg: 'var(--color-bg-tertiary)',
    text: 'var(--color-text-secondary)',
    dot: 'var(--color-text-muted)'
  },
  success: {
    bg: 'var(--color-success-muted)',
    text: 'var(--color-success)',
    dot: 'var(--color-success)'
  },
  warning: {
    bg: 'var(--color-warning-muted)',
    text: 'var(--color-warning)',
    dot: 'var(--color-warning)'
  },
  danger: {
    bg: 'var(--color-danger-muted)',
    text: 'var(--color-danger)',
    dot: 'var(--color-danger)'
  },
  critical: {
    bg: 'var(--color-critical-muted)',
    text: 'var(--color-critical)',
    dot: 'var(--color-critical)'
  },
  info: {
    bg: 'oklch(0.35 0.08 230)',
    text: 'var(--color-info)',
    dot: 'var(--color-info)'
  },
  accent: {
    bg: 'oklch(0.30 0.10 250)',
    text: 'var(--color-accent)',
    dot: 'var(--color-accent)'
  }
}

export default function Badge({ children, variant = 'default', size = 'sm', dot }: BadgeProps) {
  const colors = variantMap[variant]

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        padding: size === 'sm' ? '2px 8px' : '4px 12px',
        fontSize: size === 'sm' ? '0.6875rem' : '0.75rem',
        fontWeight: 600,
        fontFamily: 'var(--font-sans)',
        letterSpacing: '0.02em',
        textTransform: 'uppercase',
        borderRadius: 'var(--radius-full)',
        background: colors.bg,
        color: colors.text,
        whiteSpace: 'nowrap'
      }}
    >
      {dot && (
        <span
          style={{
            width: 6,
            height: 6,
            borderRadius: '50%',
            background: colors.dot,
            flexShrink: 0
          }}
        />
      )}
      {children}
    </span>
  )
}
