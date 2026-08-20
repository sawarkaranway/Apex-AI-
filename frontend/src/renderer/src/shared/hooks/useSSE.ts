/* ═══════════════════════════════════════════════════════════
   useSSE Hook — Server-Sent Events wrapper
   ═══════════════════════════════════════════════════════════ */

import { useCallback, useRef } from 'react'
import type { SSEEventType } from '@/shared/types'

interface SSEHandlers {
  onEvent: (type: SSEEventType, data: unknown) => void
  onError?: (error: Event) => void
  onOpen?: () => void
}

export function useSSE() {
  const eventSourceRef = useRef<EventSource | null>(null)

  const connect = useCallback((url: string, handlers: SSEHandlers) => {
    // Close existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
    }

    const es = new EventSource(url)
    eventSourceRef.current = es

    es.onopen = () => {
      handlers.onOpen?.()
    }

    es.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data)
        handlers.onEvent(parsed.type, parsed.data)
      } catch {
        handlers.onEvent('message_delta', event.data)
      }
    }

    // Listen for typed events
    const eventTypes: SSEEventType[] = [
      'message_start',
      'message_delta',
      'message_complete',
      'tool_call_start',
      'tool_call_result',
      'approval_required',
      'thinking_start',
      'thinking_end',
      'error',
      'done'
    ]

    eventTypes.forEach((type) => {
      es.addEventListener(type, (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data)
          handlers.onEvent(type, data)
        } catch {
          handlers.onEvent(type, event.data)
        }
      })
    })

    es.onerror = (error) => {
      handlers.onError?.(error)
      es.close()
    }

    return es
  }, [])

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
  }, [])

  return { connect, disconnect }
}
