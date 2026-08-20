/* ═══════════════════════════════════════════════════════════
   Sidebar Component — Aegis AI
   ═══════════════════════════════════════════════════════════ */

import { useState } from 'react'
import ConversationList from './ConversationList'
import NewChatButton from './NewChatButton'
import type { Conversation } from '@/shared/types'
import logoImg from '@/assets/logo.png'
import { useAuth } from '@/shared/context/AuthContext'

interface SidebarProps {
  conversations: Conversation[]
  activeConversationId: string | null
  onSelectConversation: (id: string) => void
  onNewChat: () => void
  collapsed?: boolean
  onToggleCollapse?: () => void
  onOpenSettings?: () => void
  onOpenCalculator?: () => void
  onOpenKnowledge?: () => void
}

export default function Sidebar({
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewChat,
  collapsed = false,
  onToggleCollapse,
  onOpenSettings,
  onOpenCalculator,
  onOpenKnowledge
}: SidebarProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const { user, logout } = useAuth()

  const filteredConversations = conversations.filter((c) =>
    c.title.toLowerCase().includes(searchQuery.toLowerCase())
  )

  if (collapsed) {
    return (
      <div
        style={{
          width: 56,
          height: '100%',
          background: 'var(--color-bg-secondary)',
          borderRight: '1px solid var(--color-border)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          padding: '12px 0',
          gap: 12,
          flexShrink: 0
        }}
      >
        <button
          onClick={onToggleCollapse}
          title="Expand sidebar"
          style={{
            width: 36,
            height: 36,
            borderRadius: 'var(--radius-md)',
            border: 'none',
            background: 'transparent',
            color: 'var(--color-text-secondary)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'background 0.2s'
          }}
          onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--color-bg-hover)')}
          onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M9 18l6-6-6-6" />
          </svg>
        </button>

        <div
          onClick={onNewChat}
          title="New Chat"
          style={{
            width: 36,
            height: 36,
            borderRadius: 'var(--radius-md)',
            background: 'var(--color-accent-gradient)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            boxShadow: 'var(--shadow-glow)'
          }}
        >
          <img src={logoImg} alt="Logo" style={{ width: 22, height: 22, objectFit: 'contain' }} />
        </div>

        {/* Collapsed Calculator button */}
        <button
          onClick={onOpenCalculator}
          title="Scientific Calculator & Math Engine"
          style={{
            width: 36,
            height: 36,
            borderRadius: 'var(--radius-md)',
            border: 'none',
            background: 'transparent',
            color: 'var(--color-text-secondary)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1rem',
            fontWeight: 700,
            transition: 'background 0.2s'
          }}
          onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--color-bg-hover)')}
          onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
        >
          ∑
        </button>

        {/* Collapsed Knowledge button */}
        <button
          onClick={onOpenKnowledge}
          title="Knowledge Base & RAG"
          style={{
            width: 36,
            height: 36,
            borderRadius: 'var(--radius-md)',
            border: 'none',
            background: 'transparent',
            color: 'var(--color-text-secondary)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1rem',
            transition: 'background 0.2s'
          }}
          onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--color-bg-hover)')}
          onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
        >
          📚
        </button>

        <div style={{ flex: 1 }} />

        {/* Collapsed Settings button */}
        <button
          onClick={onOpenSettings}
          title="Settings & Cloud Sync"
          style={{
            width: 36,
            height: 36,
            borderRadius: 'var(--radius-md)',
            border: 'none',
            background: 'transparent',
            color: 'var(--color-text-secondary)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'background 0.2s'
          }}
          onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--color-bg-hover)')}
          onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="3"></circle>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
          </svg>
        </button>
      </div>
    )
  }

  return (
    <div
      style={{
        width: 260,
        height: '100%',
        background: 'var(--color-bg-secondary)',
        borderRight: '1px solid var(--color-border)',
        display: 'flex',
        flexDirection: 'column',
        flexShrink: 0,
        transition: 'width 0.2s ease'
      }}
    >
      {/* Brand Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '14px 16px',
          borderBottom: '1px solid var(--color-border-subtle)'
        }}
      >
        <button
          onClick={onToggleCollapse}
          title="Collapse sidebar"
          style={{
            width: 28,
            height: 28,
            borderRadius: 'var(--radius-sm)',
            border: 'none',
            background: 'transparent',
            color: 'var(--color-text-muted)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'color 0.2s'
          }}
          onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--color-text-primary)')}
          onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--color-text-muted)')}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M15 18l-6-6 6-6" />
          </svg>
        </button>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            flex: 1,
            marginLeft: 8
          }}
        >
          <img
            src={logoImg}
            alt="Chaitanya Karya Logo"
            style={{
              width: 32,
              height: 32,
              borderRadius: 'var(--radius-md)',
              objectFit: 'contain'
            }}
          />
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span
              style={{
                fontSize: '0.9rem',
                fontWeight: 700,
                color: 'var(--color-text-primary)',
                letterSpacing: '-0.01em',
                lineHeight: 1.2
              }}
            >
              Chaitanya Karya
            </span>
            <span
              style={{
                fontSize: '0.65rem',
                fontWeight: 500,
                color: 'var(--color-accent)',
                letterSpacing: '0.02em',
                lineHeight: 1.2
              }}
            >
              Intelligence into Action
            </span>
          </div>
        </div>
      </div>

      {/* New Chat */}
      <div style={{ padding: '12px 12px 6px' }}>
        <NewChatButton onClick={onNewChat} />
      </div>

      {/* Quick Tools: Calculator & Knowledge Base */}
      <div style={{ padding: '0 12px 8px', display: 'flex', gap: 6 }}>
        <button
          onClick={onOpenCalculator}
          style={{
            flex: 1,
            padding: '7px 8px',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--color-border-subtle)',
            background: 'var(--color-bg-tertiary)',
            color: 'var(--color-text-primary)',
            fontSize: '0.75rem',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 6,
            transition: 'all 0.15s'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = 'var(--color-accent)'
            e.currentTarget.style.background = 'var(--color-bg-hover)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = 'var(--color-border-subtle)'
            e.currentTarget.style.background = 'var(--color-bg-tertiary)'
          }}
        >
          <span style={{ color: '#38BDF8', fontWeight: 700 }}>∑</span>
          <span>Calculator</span>
        </button>

        <button
          onClick={onOpenKnowledge}
          style={{
            flex: 1,
            padding: '7px 8px',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--color-border-subtle)',
            background: 'var(--color-bg-tertiary)',
            color: 'var(--color-text-primary)',
            fontSize: '0.75rem',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 6,
            transition: 'all 0.15s'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = 'var(--color-accent)'
            e.currentTarget.style.background = 'var(--color-bg-hover)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = 'var(--color-border-subtle)'
            e.currentTarget.style.background = 'var(--color-bg-tertiary)'
          }}
        >
          <span>📚</span>
          <span>Knowledge</span>
        </button>
      </div>

      {/* Search */}
      <div style={{ padding: '0 12px 8px' }}>
        <div
          style={{
            position: 'relative',
            display: 'flex',
            alignItems: 'center'
          }}
        >
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="var(--color-text-muted)"
            strokeWidth="2"
            strokeLinecap="round"
            style={{ position: 'absolute', left: 10, pointerEvents: 'none' }}
          >
            <circle cx="11" cy="11" r="8" />
            <path d="M21 21l-4.35-4.35" />
          </svg>
          <input
            type="text"
            placeholder="Search conversations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              width: '100%',
              padding: '8px 12px 8px 32px',
              background: 'var(--color-bg-tertiary)',
              border: '1px solid var(--color-border-subtle)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--color-text-primary)',
              fontSize: '0.8125rem',
              outline: 'none',
              fontFamily: 'var(--font-sans)',
              transition: 'border-color 0.2s'
            }}
            onFocus={(e) => (e.currentTarget.style.borderColor = 'var(--color-border-focus)')}
            onBlur={(e) => (e.currentTarget.style.borderColor = 'var(--color-border-subtle)')}
          />
        </div>
      </div>

      {/* Conversation List */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '0 8px' }}>
        <ConversationList
          conversations={filteredConversations}
          activeId={activeConversationId}
          onSelect={onSelectConversation}
        />
      </div>

      {/* Footer */}
      <div
        style={{
          padding: '12px 16px',
          borderTop: '1px solid var(--color-border-subtle)',
          display: 'flex',
          alignItems: 'center',
          gap: 8
        }}
      >
        <div
          style={{
            width: 28,
            height: 28,
            borderRadius: 'var(--radius-md)',
            background: 'var(--color-bg-tertiary)',
            border: '1px solid var(--color-border-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '0.75rem',
            fontWeight: 600,
            color: 'var(--color-text-secondary)'
          }}
        >
          {user?.first_name ? user.first_name[0].toUpperCase() : user?.email ? user.email[0].toUpperCase() : 'U'}
        </div>
        <span
          style={{
            fontSize: '0.8125rem',
            color: 'var(--color-text-secondary)',
            flex: 1,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap'
          }}
        >
          {user?.first_name || user?.email || 'User'}
        </span>

        {/* Settings button */}
        <button
          aria-label="Settings"
          title="Settings & Cloud Sync"
          onClick={onOpenSettings}
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--color-text-muted)',
            cursor: 'pointer',
            padding: 4,
            borderRadius: 'var(--radius-sm)',
            display: 'flex',
            transition: 'color 0.2s'
          }}
          onMouseEnter={(e) => (e.currentTarget.style.color = '#38BDF8')}
          onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--color-text-muted)')}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="3"></circle>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
          </svg>
        </button>

        {/* Logout button */}
        <button
          aria-label="Logout"
          title="Logout"
          onClick={() => logout()}
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--color-text-muted)',
            cursor: 'pointer',
            padding: 4,
            borderRadius: 'var(--radius-sm)',
            display: 'flex',
            transition: 'color 0.2s'
          }}
          onMouseEnter={(e) => (e.currentTarget.style.color = '#ff6b6b')}
          onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--color-text-muted)')}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
            <polyline points="16 17 21 12 16 7"></polyline>
            <line x1="21" y1="12" x2="9" y2="12"></line>
          </svg>
        </button>
      </div>
    </div>
  )
}
