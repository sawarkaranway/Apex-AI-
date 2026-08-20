/* ═══════════════════════════════════════════════════════════
   useApi Hook — Wrapper for API calls with loading/error
   ═══════════════════════════════════════════════════════════ */

import { useState, useCallback } from 'react'
import api from '@/shared/lib/api'

interface UseApiState<T> {
  data: T | null
  loading: boolean
  error: string | null
}

export function useApi<T>() {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: false,
    error: null
  })

  const get = useCallback(async (endpoint: string) => {
    setState((prev) => ({ ...prev, loading: true, error: null }))
    try {
      const data = await api.get<T>(endpoint)
      setState({ data, loading: false, error: null })
      return data
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error'
      setState((prev) => ({ ...prev, loading: false, error: message }))
      throw err
    }
  }, [])

  const post = useCallback(async (endpoint: string, body?: unknown) => {
    setState((prev) => ({ ...prev, loading: true, error: null }))
    try {
      const data = await api.post<T>(endpoint, body)
      setState({ data, loading: false, error: null })
      return data
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error'
      setState((prev) => ({ ...prev, loading: false, error: message }))
      throw err
    }
  }, [])

  return { ...state, get, post }
}
