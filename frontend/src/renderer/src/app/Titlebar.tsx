/* ═══════════════════════════════════════════════════════════
   Titlebar Component — Custom frameless window titlebar
   ═══════════════════════════════════════════════════════════ */

import { useState } from 'react'
import { APP_NAME } from '@/shared/lib/constants'

export default function Titlebar() {
  const [isMaximized, setIsMaximized] = useState(false)

  const handleMinimize = () => {
    window.electron?.ipcRenderer.send('window:minimize')
  }

  const handleMaximize = () => {
    window.electron?.ipcRenderer.send('window:maximize')
    setIsMaximized(!isMaximized)
  }

  const handleClose = () => {
    window.electron?.ipcRenderer.send('window:close')
  }

  return (
    <div
      className="titlebar-drag"
      style={{
        height: 'var(--titlebar-height)',
        background: 'var(--color-bg-secondary)',
        borderBottom: '1px solid var(--color-border-subtle)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 8px 0 16px',
        flexShrink: 0,
        userSelect: 'none',
        zIndex: 100
      }}
    >
      {/* App title */}
      <span
        style={{
          fontSize: '0.75rem',
          fontWeight: 500,
          color: 'var(--color-text-muted)',
          letterSpacing: '0.02em'
        }}
      >
        {APP_NAME}
      </span>

      {/* Window controls */}
      <div
        className="titlebar-no-drag"
        style={{
          display: 'flex',
          gap: 2
        }}
      >
        {/* Minimize */}
        <button
          onClick={handleMinimize}
          aria-label="Minimize"
          style={controlButtonStyle}
          onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--color-bg-hover)')}
          onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
        >
          <svg width="12" height="12" viewBox="0 0 12 12">
            <rect y="5" width="12" height="1.5" rx="0.75" fill="currentColor" />
          </svg>
        </button>

        {/* Maximize / Restore */}
        <button
          onClick={handleMaximize}
          aria-label={isMaximized ? 'Restore' : 'Maximize'}
          style={controlButtonStyle}
          onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--color-bg-hover)')}
          onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
        >
          {isMaximized ? (
            <svg width="12" height="12" viewBox="0 0 12 12">
              <rect x="1.5" y="3" width="7.5" height="7.5" rx="1" stroke="currentColor" strokeWidth="1.3" fill="none" />
              <path d="M3.5 3V1.75A1 1 0 0 1 4.5.75h6a1 1 0 0 1 1 1v6a1 1 0 0 1-1 1H9" stroke="currentColor" strokeWidth="1.3" fill="none" />
            </svg>
          ) : (
            <svg width="12" height="12" viewBox="0 0 12 12">
              <rect x="1" y="1" width="10" height="10" rx="1.5" stroke="currentColor" strokeWidth="1.3" fill="none" />
            </svg>
          )}
        </button>

        {/* Close */}
        <button
          onClick={handleClose}
          aria-label="Close"
          style={{
            ...controlButtonStyle,
            borderRadius: 'var(--radius-sm)'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'var(--color-danger)'
            e.currentTarget.style.color = 'white'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'transparent'
            e.currentTarget.style.color = 'var(--color-text-muted)'
          }}
        >
          <svg width="12" height="12" viewBox="0 0 12 12">
            <path d="M2 2l8 8M10 2l-8 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </button>
      </div>
    </div>
  )
}

const controlButtonStyle: React.CSSProperties = {
  width: 34,
  height: 28,
  background: 'transparent',
  border: 'none',
  borderRadius: 'var(--radius-sm)',
  color: 'var(--color-text-muted)',
  cursor: 'pointer',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  transition: 'all 0.15s'
}
