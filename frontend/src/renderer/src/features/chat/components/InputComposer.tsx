/* ═══════════════════════════════════════════════════════════
   InputComposer Component — Rich input area with Voice STT
   ═══════════════════════════════════════════════════════════ */

import { useState, useRef, useCallback, useEffect } from 'react'

interface InputComposerProps {
  onSubmit: (content: string) => void
  disabled?: boolean
  placeholder?: string
}

export default function InputComposer({
  onSubmit,
  disabled = false,
  placeholder = 'Ask Chaitanya Karya anything...'
}: InputComposerProps) {
  const [value, setValue] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const recognitionRef = useRef<any>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])

  const adjustHeight = useCallback(() => {
    const ta = textareaRef.current
    if (ta) {
      ta.style.height = 'auto'
      ta.style.height = `${Math.min(ta.scrollHeight, 200)}px`
    }
  }, [])

  // Initialize Speech Recognition
  useEffect(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition()
      recognition.continuous = true
      recognition.interimResults = true
      recognition.lang = 'en-US'

      recognition.onresult = (event: any) => {
        let transcript = ''
        for (let i = event.resultIndex; i < event.results.length; i++) {
          transcript += event.results[i][0].transcript
        }
        setValue((prev) => {
          const cleanPrev = prev.trim()
          return cleanPrev ? `${cleanPrev} ${transcript.trim()}` : transcript.trim()
        })
        adjustHeight()
      }

      recognition.onerror = (err: any) => {
        console.warn('Speech recognition error:', err)
        setIsRecording(false)
      }

      recognition.onend = () => {
        setIsRecording(false)
      }

      recognitionRef.current = recognition
    }
  }, [adjustHeight])

  const toggleVoiceRecording = async () => {
    if (isRecording) {
      // Stop recording
      if (recognitionRef.current) {
        recognitionRef.current.stop()
      }
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop()
      }
      setIsRecording(false)
      return
    }

    // Start recording
    if (recognitionRef.current) {
      try {
        recognitionRef.current.start()
        setIsRecording(true)
        return
      } catch (e) {
        console.warn('Recognition start failed, trying MediaRecorder:', e)
      }
    }

    // Fallback: MediaRecorder sending to backend /api/voice/stt/
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      audioChunksRef.current = []

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' })
        stream.getTracks().forEach((track) => track.stop())

        try {
          const arrayBuffer = await audioBlob.arrayBuffer()
          const response = await fetch('http://127.0.0.1:8000/api/voice/stt/', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/octet-stream'
            },
            body: arrayBuffer
          })
          const data = await response.json()
          if (data.transcription) {
            setValue((prev) => (prev ? `${prev} ${data.transcription}` : data.transcription))
            adjustHeight()
          }
        } catch (err) {
          console.error('Backend STT failed:', err)
        }
      }

      mediaRecorder.start()
      mediaRecorderRef.current = mediaRecorder
      setIsRecording(true)
    } catch (err) {
      console.warn('Microphone access denied:', err)
      alert('Microphone access is required for voice input.')
    }
  }

  const handleSubmit = useCallback(() => {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    if (isRecording) {
      toggleVoiceRecording()
    }
    onSubmit(trimmed)
    setValue('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }, [value, disabled, isRecording, onSubmit])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div
      style={{
        background: 'var(--color-bg-secondary)',
        border: `1px solid ${isRecording ? '#ef4444' : 'var(--color-border)'}`,
        borderRadius: 'var(--radius-xl)',
        padding: '4px 4px 4px 16px',
        display: 'flex',
        alignItems: 'flex-end',
        gap: 8,
        transition: 'border-color 0.2s, box-shadow 0.2s',
        boxShadow: isRecording ? '0 0 15px rgba(239, 68, 68, 0.4)' : 'var(--shadow-sm)'
      }}
      onFocus={(e) => {
        const el = e.currentTarget
        if (!isRecording) {
          el.style.borderColor = 'var(--color-border-focus)'
          el.style.boxShadow = 'var(--shadow-glow)'
        }
      }}
      onBlur={(e) => {
        const el = e.currentTarget
        if (!el.contains(e.relatedTarget as Node) && !isRecording) {
          el.style.borderColor = 'var(--color-border)'
          el.style.boxShadow = 'var(--shadow-sm)'
        }
      }}
    >
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => {
          setValue(e.target.value)
          adjustHeight()
        }}
        onKeyDown={handleKeyDown}
        placeholder={isRecording ? '🎙️ Listening... speak now...' : placeholder}
        disabled={disabled}
        rows={1}
        id="chat-input"
        style={{
          flex: 1,
          background: 'transparent',
          border: 'none',
          outline: 'none',
          color: 'var(--color-text-primary)',
          fontSize: '0.875rem',
          fontFamily: 'var(--font-sans)',
          lineHeight: 1.5,
          resize: 'none',
          padding: '10px 0',
          maxHeight: 200,
          minHeight: 20,
          userSelect: 'text'
        }}
      />

      {/* Action buttons */}
      <div style={{ display: 'flex', gap: 4, padding: '4px 0', alignItems: 'center' }}>
        {/* Voice button */}
        <button
          onClick={toggleVoiceRecording}
          type="button"
          aria-label={isRecording ? 'Stop recording' : 'Start voice input'}
          disabled={disabled}
          title={isRecording ? 'Stop listening' : 'Voice input (Speak)'}
          style={{
            width: 36,
            height: 36,
            borderRadius: 'var(--radius-lg)',
            background: isRecording ? '#ef4444' : 'transparent',
            border: 'none',
            color: isRecording ? '#ffffff' : 'var(--color-text-muted)',
            cursor: disabled ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.2s',
            animation: isRecording ? 'pulse 1.5s infinite' : 'none',
            opacity: disabled ? 0.4 : 1
          }}
          onMouseEnter={(e) => {
            if (!disabled && !isRecording) {
              e.currentTarget.style.background = 'var(--color-bg-hover)'
              e.currentTarget.style.color = 'var(--color-text-primary)'
            }
          }}
          onMouseLeave={(e) => {
            if (!isRecording) {
              e.currentTarget.style.background = 'transparent'
              e.currentTarget.style.color = 'var(--color-text-muted)'
            }
          }}
        >
          {isRecording ? (
            <span style={{ fontSize: '14px', fontWeight: 'bold' }}>⏹</span>
          ) : (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <rect x="9" y="1" width="6" height="13" rx="3" />
              <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
              <path d="M12 19v4M8 23h8" />
            </svg>
          )}
        </button>

        {/* Send button */}
        <button
          onClick={handleSubmit}
          disabled={disabled || !value.trim()}
          id="send-button"
          aria-label="Send message"
          style={{
            width: 36,
            height: 36,
            borderRadius: 'var(--radius-lg)',
            background:
              value.trim() && !disabled ? 'var(--color-accent)' : 'var(--color-bg-tertiary)',
            border: 'none',
            color: value.trim() && !disabled ? 'white' : 'var(--color-text-muted)',
            cursor: disabled || !value.trim() ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.2s',
            boxShadow:
              value.trim() && !disabled ? 'var(--shadow-glow)' : 'none'
          }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
          </svg>
        </button>
      </div>
    </div>
  )
}

