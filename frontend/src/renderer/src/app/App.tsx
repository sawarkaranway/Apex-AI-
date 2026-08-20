import { useState, useEffect, useCallback } from 'react'
import Titlebar from './Titlebar'
import Sidebar from '@/features/sidebar/components/Sidebar'
import ChatView from '@/features/chat/components/ChatView'
import SettingsModal from '@/features/settings/SettingsModal'
import CalculatorModal from '@/features/calculator/CalculatorModal'
import KnowledgeBaseModal from '@/features/knowledge/KnowledgeBaseModal'
import api from '@/shared/lib/api'
import type { Conversation, Message, ApprovalRequest } from '@/shared/types'

export default function App() {
  // ── State ──
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [isThinking, setIsThinking] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [pendingApproval, setPendingApproval] = useState<ApprovalRequest | null>(null)
  const [isSettingsOpen, setIsSettingsOpen] = useState(false)
  const [isCalculatorOpen, setIsCalculatorOpen] = useState(false)
  const [isKnowledgeOpen, setIsKnowledgeOpen] = useState(false)

  // ── Fetch Conversations on Mount ──
  useEffect(() => {
    async function loadConversations() {
      try {
        const data = await api.get<Conversation[] | { results: Conversation[] }>('/conversations/')
        const list = Array.isArray(data) ? data : data.results || []
        setConversations(list)
        if (list.length > 0 && !activeConversationId) {
          setActiveConversationId(list[0].id)
        }
      } catch (err) {
        console.warn('Could not fetch conversations from backend:', err)
      }
    }
    loadConversations()
  }, [])

  // ── Fetch Messages when active conversation changes ──
  useEffect(() => {
    if (!activeConversationId) {
      setMessages([])
      return
    }
    async function loadMessages() {
      try {
        const data = await api.get<Message[] | { results: Message[] }>(`/messages/?conversation_id=${activeConversationId}`)
        const list = Array.isArray(data) ? data : data.results || []
        setMessages(list)
      } catch (err) {
        console.warn('Could not fetch messages for conversation:', err)
      }
    }
    loadMessages()
  }, [activeConversationId])

  // ── Get active messages ──
  const activeMessages = messages.filter(
    (m) => m.conversation_id === activeConversationId
  )

  // Check for pending approval
  const activePendingApproval = activeMessages
    .flatMap((m) => (m.approval_request ? [m.approval_request] : []))
    .find((a) => a.status === 'pending') || pendingApproval

  // ── Send message ──
  const handleSendMessage = useCallback(
    async (content: string) => {
      const convId = activeConversationId || `conv-${Date.now()}`

      if (!activeConversationId) {
        const newConv: Conversation = {
          id: convId,
          title: content.slice(0, 50),
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          message_count: 0,
          last_message_preview: content
        }
        setConversations((prev) => [newConv, ...prev])
        setActiveConversationId(convId)
      }

      const userMsg: Message = {
        id: `msg-${Date.now()}`,
        conversation_id: convId,
        role: 'user',
        content,
        status: 'complete',
        created_at: new Date().toISOString()
      }
      setMessages((prev) => [...prev, userMsg])
      setIsThinking(true)

      try {
        const data = await api.post<{
          user_message: Message
          assistant_message: Message
          conversation_id: string
        }>('/chat/', {
          content,
          conversation_id: convId
        })

        setIsThinking(false)
        if (data.assistant_message) {
          setMessages((prev) => [...prev, data.assistant_message])
          if (data.assistant_message.approval_request) {
            setPendingApproval(data.assistant_message.approval_request)
          }

          const msgContent = data.assistant_message.content || ''
          const urlMatch = msgContent.match(/https?:\/\/[^\s']+/);
          if (urlMatch && urlMatch[0]) {
            const targetUrl = urlMatch[0]
            try {
              if (window.electron && window.electron.ipcRenderer) {
                window.electron.ipcRenderer.invoke('shell:open_external', targetUrl)
              } else {
                window.open(targetUrl, '_blank')
              }
            } catch {
              window.open(targetUrl, '_blank')
            }
          }
        }
      } catch (err: unknown) {
        console.error('Error connecting to Chaitanya Karya Django API backend:', err)
        setIsThinking(false)
        const errMsg = err instanceof Error ? err.message : String(err)
        const assistantMsgId = `msg-${Date.now()}-err`
        const assistantMsg: Message = {
          id: assistantMsgId,
          conversation_id: convId,
          role: 'assistant',
          content: `Backend Communication Error: ${errMsg}\n\nPlease verify that the Python Django backend server is active at http://127.0.0.1:8000/api.`,
          status: 'complete',
          created_at: new Date().toISOString()
        }
        setMessages((prev) => [...prev, assistantMsg])
      }
    },
    [activeConversationId]
  )

  // ── Approval response ──
  const handleApprovalResponse = useCallback(
    async (id: string, approved: boolean, reason?: string) => {
      setMessages((prev) =>
        prev.map((m) => {
          if (m.approval_request?.id === id) {
            return {
              ...m,
              approval_request: {
                ...m.approval_request,
                status: approved ? 'approved' : 'rejected',
                resolved_at: new Date().toISOString(),
                rejection_reason: reason
              }
            }
          }
          return m
        })
      )
      setPendingApproval(null)

      try {
        const res = await api.post<{ followup_content: string }>(
          `/approvals/${id}/resolve/`,
          { approved, reason }
        )

        const followUp: Message = {
          id: `msg-${Date.now()}-follow`,
          conversation_id: activeConversationId || '',
          role: 'assistant',
          content: res.followup_content,
          status: 'complete',
          created_at: new Date().toISOString()
        }
        setMessages((prev) => [...prev, followUp])
      } catch (err) {
        console.warn('Backend approval resolution error:', err)
        const followUp: Message = {
          id: `msg-${Date.now()}-follow`,
          conversation_id: activeConversationId || '',
          role: 'assistant',
          content: approved
            ? '✅ Action **approved** and recorded by backend.'
            : `❌ Action **rejected**${reason ? `: ${reason}` : ''}. The action was cancelled.`,
          status: 'complete',
          created_at: new Date().toISOString()
        }
        setMessages((prev) => [...prev, followUp])
      }
    },
    [activeConversationId]
  )

  // ── New chat ──
  const handleNewChat = useCallback(() => {
    setActiveConversationId(null)
    setMessages([])
  }, [])

  // ── Select conversation ──
  const handleSelectConversation = useCallback((id: string) => {
    setActiveConversationId(id)
  }, [])

  return (
    <div
      style={{
        width: '100vw',
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        background: 'var(--color-bg-primary)',
        overflow: 'hidden'
      }}
    >
      {/* Custom titlebar */}
      <Titlebar />

      {/* Main content */}
      <div
        style={{
          flex: 1,
          display: 'flex',
          overflow: 'hidden'
        }}
      >
        {/* Sidebar */}
        <Sidebar
          conversations={conversations}
          activeConversationId={activeConversationId}
          onSelectConversation={handleSelectConversation}
          onNewChat={handleNewChat}
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
          onOpenSettings={() => setIsSettingsOpen(true)}
          onOpenCalculator={() => setIsCalculatorOpen(true)}
          onOpenKnowledge={() => setIsKnowledgeOpen(true)}
        />

        {/* Chat area */}
        <ChatView
          messages={activeMessages}
          isStreaming={false}
          isThinking={isThinking}
          onSendMessage={handleSendMessage}
          onApprovalResponse={handleApprovalResponse}
          pendingApproval={activePendingApproval || null}
        />
      </div>

      {/* Settings & Cloud Sync Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />

      {/* Scientific Calculator Modal */}
      <CalculatorModal
        isOpen={isCalculatorOpen}
        onClose={() => setIsCalculatorOpen(false)}
        onPasteToChat={(text) => handleSendMessage(text)}
      />

      {/* Grounded Knowledge Base RAG Modal */}
      <KnowledgeBaseModal
        isOpen={isKnowledgeOpen}
        onClose={() => setIsKnowledgeOpen(false)}
        onInsertContextToChat={(text) => handleSendMessage(text)}
      />
    </div>
  )
}

