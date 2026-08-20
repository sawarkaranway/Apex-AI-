/* ═══════════════════════════════════════════════════════════
   ApprovalModal Component — Human-in-the-loop approval
   ═══════════════════════════════════════════════════════════ */

import { useState } from 'react'
import Badge from '@/shared/components/Badge'
import Button from '@/shared/components/Button'
import Modal from '@/shared/components/Modal'
import { RISK_COLORS } from '@/shared/lib/constants'
import type { ApprovalRequest, RiskLevel } from '@/shared/types'

interface ApprovalModalProps {
  request: ApprovalRequest
  onRespond: (id: string, approved: boolean, reason?: string) => void
  inline?: boolean
}

const riskVariantMap: Record<RiskLevel, 'success' | 'warning' | 'danger' | 'critical'> = {
  LOW: 'success',
  MEDIUM: 'warning',
  HIGH: 'danger',
  CRITICAL: 'critical'
}

export default function ApprovalModal({
  request,
  onRespond,
  inline = false
}: ApprovalModalProps) {
  const [rejectionReason, setRejectionReason] = useState('')
  const [showRejectInput, setShowRejectInput] = useState(false)
  const riskColors = RISK_COLORS[request.risk_level]

  const content = (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Risk banner */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          padding: '12px 16px',
          background: riskColors.bg,
          borderRadius: 'var(--radius-lg)',
          border: `1px solid ${riskColors.text}33`
        }}
      >
        <div
          style={{
            width: 36,
            height: 36,
            borderRadius: 'var(--radius-md)',
            background: `${riskColors.text}22`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.125rem'
          }}
        >
          {request.risk_level === 'CRITICAL' ? '🛑' : request.risk_level === 'HIGH' ? '⚠️' : '🔔'}
        </div>
        <div style={{ flex: 1 }}>
          <div
            style={{
              fontSize: '0.8125rem',
              fontWeight: 600,
              color: riskColors.text,
              marginBottom: 2
            }}
          >
            {riskColors.label} — Action Requires Approval
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
            This action has been classified as {request.risk_level.toLowerCase()} risk
          </div>
        </div>
        <Badge variant={riskVariantMap[request.risk_level]} size="md">
          {request.risk_level}
        </Badge>
      </div>

      {/* Action details */}
      <div>
        <div
          style={{
            fontSize: '0.6875rem',
            fontWeight: 600,
            color: 'var(--color-text-muted)',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            marginBottom: 8
          }}
        >
          Action Details
        </div>
        <div
          style={{
            background: 'var(--color-bg-tertiary)',
            borderRadius: 'var(--radius-md)',
            padding: '12px 16px'
          }}
        >
          <div
            style={{
              fontSize: '0.875rem',
              fontWeight: 500,
              color: 'var(--color-text-primary)',
              marginBottom: 4
            }}
          >
            {request.tool_display_name}
          </div>
          <div
            style={{
              fontSize: '0.8125rem',
              color: 'var(--color-text-secondary)',
              lineHeight: 1.5
            }}
          >
            {request.description}
          </div>
        </div>
      </div>

      {/* Impact summary */}
      <div>
        <div
          style={{
            fontSize: '0.6875rem',
            fontWeight: 600,
            color: 'var(--color-text-muted)',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            marginBottom: 8
          }}
        >
          What will happen
        </div>
        <div
          style={{
            fontSize: '0.8125rem',
            color: 'var(--color-text-secondary)',
            lineHeight: 1.6,
            padding: '0 4px'
          }}
        >
          {request.impact_summary}
        </div>
      </div>

      {/* Arguments */}
      {Object.keys(request.arguments).length > 0 && (
        <div>
          <div
            style={{
              fontSize: '0.6875rem',
              fontWeight: 600,
              color: 'var(--color-text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              marginBottom: 8
            }}
          >
            Parameters
          </div>
          <pre
            style={{
              background: 'var(--color-bg-primary)',
              border: '1px solid var(--color-border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '10px 12px',
              fontSize: '0.75rem',
              fontFamily: 'var(--font-mono)',
              color: 'var(--color-text-secondary)',
              overflowX: 'auto',
              margin: 0,
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-all'
            }}
          >
            {JSON.stringify(request.arguments, null, 2)}
          </pre>
        </div>
      )}

      {/* Rejection reason */}
      {showRejectInput && (
        <div>
          <div
            style={{
              fontSize: '0.6875rem',
              fontWeight: 600,
              color: 'var(--color-text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              marginBottom: 8
            }}
          >
            Rejection Reason {request.risk_level === 'CRITICAL' ? '(required)' : '(optional)'}
          </div>
          <textarea
            value={rejectionReason}
            onChange={(e) => setRejectionReason(e.target.value)}
            placeholder="Why are you rejecting this action?"
            style={{
              width: '100%',
              padding: '10px 12px',
              background: 'var(--color-bg-primary)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--color-text-primary)',
              fontSize: '0.8125rem',
              fontFamily: 'var(--font-sans)',
              outline: 'none',
              resize: 'vertical',
              minHeight: 60
            }}
          />
        </div>
      )}

      {/* Action buttons */}
      <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end', paddingTop: 4 }}>
        {showRejectInput ? (
          <>
            <Button
              variant="ghost"
              size="md"
              onClick={() => setShowRejectInput(false)}
            >
              Back
            </Button>
            <Button
              variant="danger"
              size="md"
              onClick={() => onRespond(request.id, false, rejectionReason)}
              disabled={request.risk_level === 'CRITICAL' && !rejectionReason.trim()}
            >
              Confirm Rejection
            </Button>
          </>
        ) : (
          <>
            <Button
              variant="ghost"
              size="md"
              onClick={() => setShowRejectInput(true)}
            >
              ✕ Reject
            </Button>
            <Button
              variant="success"
              size="md"
              onClick={() => onRespond(request.id, true)}
            >
              ✓ Approve
            </Button>
          </>
        )}
      </div>
    </div>
  )

  if (inline) {
    return (
      <div
        style={{
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-xl)',
          padding: '16px',
          background: 'var(--color-bg-secondary)',
          animation: 'var(--animate-scale-in)'
        }}
      >
        {content}
      </div>
    )
  }

  return (
    <Modal isOpen={true} onClose={() => {}} title="Action Approval Required" width={520} showCloseButton={false}>
      {content}
    </Modal>
  )
}
