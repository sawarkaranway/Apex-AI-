/* ═══════════════════════════════════════════════════════════
   Shared TypeScript Types — Aegis AI
   ═══════════════════════════════════════════════════════════ */

// ── Conversations ──

export interface Conversation {
  id: string
  title: string
  created_at: string
  updated_at: string
  message_count: number
  last_message_preview?: string
}

// ── Messages ──

export type MessageRole = 'user' | 'assistant' | 'system'
export type MessageStatus = 'sending' | 'streaming' | 'complete' | 'error'

export interface Message {
  id: string
  conversation_id: string
  role: MessageRole
  content: string
  status: MessageStatus
  created_at: string
  tool_calls?: ToolCall[]
  approval_request?: ApprovalRequest
}

// ── Tool Calls ──

export type ToolCallStatus = 'pending' | 'running' | 'success' | 'error' | 'approval_required'

export interface ToolCall {
  id: string
  tool_name: string
  tool_display_name: string
  arguments: Record<string, unknown>
  result?: string
  status: ToolCallStatus
  started_at?: string
  completed_at?: string
  error?: string
}

// ── Approval ──

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

export interface ApprovalRequest {
  id: string
  tool_call_id: string
  tool_name: string
  tool_display_name: string
  description: string
  risk_level: RiskLevel
  arguments: Record<string, unknown>
  impact_summary: string
  created_at: string
  status: 'pending' | 'approved' | 'rejected'
  resolved_at?: string
  rejection_reason?: string
}

// ── SSE Events ──

export type SSEEventType =
  | 'message_start'
  | 'message_delta'
  | 'message_complete'
  | 'tool_call_start'
  | 'tool_call_result'
  | 'approval_required'
  | 'thinking_start'
  | 'thinking_end'
  | 'error'
  | 'done'

export interface SSEEvent {
  type: SSEEventType
  data: unknown
}

// ── Notifications ──

export type NotificationType = 'briefing' | 'email_alert' | 'calendar_reminder' | 'task_update'

export interface AppNotification {
  id: string
  type: NotificationType
  title: string
  body: string
  created_at: string
  read: boolean
  action_url?: string
}

// ── Auth ──

export interface AuthState {
  isAuthenticated: boolean
  isLoading: boolean
  user?: {
    email: string
    name: string
    picture?: string
  }
}

// ── Settings ──

export interface AppSettings {
  theme: 'dark'
  llm_provider: 'gemini' | 'deepseek' | 'qwen'
  voice_enabled: boolean
  notifications_enabled: boolean
  auto_approve_low_risk: boolean
  auto_approve_medium_risk: boolean
}
