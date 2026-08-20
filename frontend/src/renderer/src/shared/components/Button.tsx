/* ═══════════════════════════════════════════════════════════
   Button Component — Aegis AI Design System
   ═══════════════════════════════════════════════════════════ */

import { type ButtonHTMLAttributes } from 'react'

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'success'
type ButtonSize = 'sm' | 'md' | 'lg'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  loading?: boolean
  icon?: React.ReactNode
}

const variantStyles: Record<ButtonVariant, string> = {
  primary: `
    background: var(--color-accent);
    color: var(--color-text-inverse);
    border: none;
    box-shadow: var(--shadow-sm), var(--shadow-glow);
  `,
  secondary: `
    background: var(--color-bg-tertiary);
    color: var(--color-text-primary);
    border: 1px solid var(--color-border);
  `,
  ghost: `
    background: transparent;
    color: var(--color-text-secondary);
    border: 1px solid transparent;
  `,
  danger: `
    background: var(--color-danger);
    color: white;
    border: none;
  `,
  success: `
    background: var(--color-success);
    color: var(--color-text-inverse);
    border: none;
  `
}

const sizeStyles: Record<ButtonSize, React.CSSProperties> = {
  sm: { padding: '6px 12px', fontSize: '0.8125rem', borderRadius: 'var(--radius-md)' },
  md: { padding: '8px 18px', fontSize: '0.875rem', borderRadius: 'var(--radius-md)' },
  lg: { padding: '12px 24px', fontSize: '0.9375rem', borderRadius: 'var(--radius-lg)' }
}

export default function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  icon,
  children,
  disabled,
  style,
  ...props
}: ButtonProps) {
  return (
    <button
      disabled={disabled || loading}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '8px',
        fontFamily: 'var(--font-sans)',
        fontWeight: 500,
        cursor: disabled || loading ? 'not-allowed' : 'pointer',
        opacity: disabled || loading ? 0.5 : 1,
        transition: 'all 0.2s ease',
        whiteSpace: 'nowrap',
        userSelect: 'none',
        ...sizeStyles[size],
        ...style
      }}
      // Apply variant styles via CSS string
      className="ck-btn"
      data-variant={variant}
      {...props}
    >
      {loading ? <Spinner size={14} /> : icon}
      {children}
      <style>{`
        .ck-btn[data-variant="primary"] { ${variantStyles.primary} }
        .ck-btn[data-variant="secondary"] { ${variantStyles.secondary} }
        .ck-btn[data-variant="ghost"] { ${variantStyles.ghost} }
        .ck-btn[data-variant="danger"] { ${variantStyles.danger} }
        .ck-btn[data-variant="success"] { ${variantStyles.success} }
        .ck-btn:hover:not(:disabled) { filter: brightness(1.15); }
        .ck-btn:active:not(:disabled) { transform: scale(0.97); }
      `}</style>
    </button>
  )
}

function Spinner({ size = 16 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      style={{ animation: 'spin 1s linear infinite' }}
    >
      <circle
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
        opacity={0.25}
      />
      <path
        d="M12 2a10 10 0 0 1 10 10"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
      />
    </svg>
  )
}
