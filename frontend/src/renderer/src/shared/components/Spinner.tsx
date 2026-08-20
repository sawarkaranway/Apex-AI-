/* ═══════════════════════════════════════════════════════════
   Spinner Component — Aegis AI Design System
   ═══════════════════════════════════════════════════════════ */

interface SpinnerProps {
  size?: number
  color?: string
}

export default function Spinner({
  size = 20,
  color = 'var(--color-accent)'
}: SpinnerProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      style={{ animation: 'spin 0.8s linear infinite' }}
    >
      <circle
        cx="12"
        cy="12"
        r="10"
        stroke={color}
        strokeWidth="3"
        strokeLinecap="round"
        opacity={0.2}
      />
      <path
        d="M12 2a10 10 0 0 1 10 10"
        stroke={color}
        strokeWidth="3"
        strokeLinecap="round"
      />
    </svg>
  )
}
