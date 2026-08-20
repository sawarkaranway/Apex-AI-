/* ═══════════════════════════════════════════════════════════
   RiskBadge Component
   ═══════════════════════════════════════════════════════════ */

import Badge from '@/shared/components/Badge'
import type { RiskLevel } from '@/shared/types'

interface RiskBadgeProps {
  level: RiskLevel
  size?: 'sm' | 'md'
}

const riskVariantMap = {
  LOW: 'success' as const,
  MEDIUM: 'warning' as const,
  HIGH: 'danger' as const,
  CRITICAL: 'critical' as const
}

export default function RiskBadge({ level, size = 'sm' }: RiskBadgeProps) {
  return (
    <Badge variant={riskVariantMap[level]} size={size} dot>
      {level}
    </Badge>
  )
}
