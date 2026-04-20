'use client'

/**
 * Generic SSE streaming hook.
 *
 * Usage:
 *   const { messages, isStreaming, lastTrace, error, sendMessage, abort } = useStream()
 *
 * Generic enough to use for any streaming feature, not just chat.
 */

import { useState, useCallback, useRef } from 'react'
import { streamChat } from '@/lib/sse'
import type { TraceEvent } from '@/lib/types'

interface StreamState {
  messages: string[]
  isStreaming: boolean
  lastTrace: TraceEvent | null
  error: string | null
}

interface UseStreamReturn extends StreamState {
  sendMessage: (question: string) => Promise<void>
  abort: () => void
}

export function useStream(): UseStreamReturn {
  const [state, setState] = useState<StreamState>({
    messages: [],
    isStreaming: false,
    lastTrace: null,
    error: null,
  })
  const abortRef = useRef<AbortController | null>(null)

  const abort = useCallback(() => {
    abortRef.current?.abort()
  }, [])

  const sendMessage = useCallback(async (question: string) => {
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller

    // Push a new empty slot for the incoming message
    setState(prev => ({
      ...prev,
      isStreaming: true,
      error: null,
      messages: [...prev.messages, ''],
    }))

    try {
      let current = ''
      for await (const event of streamChat(question, controller.signal)) {
        if (event.type === 'token') {
          current += event.data.token
          setState(prev => {
            const messages = [...prev.messages]
            messages[messages.length - 1] = current
            return { ...prev, messages }
          })
        } else if (event.type === 'trace') {
          setState(prev => ({ ...prev, lastTrace: event.data }))
        } else if (event.type === 'error') {
          setState(prev => ({ ...prev, error: event.data.message }))
        }
      }
    } catch (err) {
      if (!(err instanceof Error && err.name === 'AbortError')) {
        setState(prev => ({ ...prev, error: String(err) }))
      }
    } finally {
      setState(prev => ({ ...prev, isStreaming: false }))
    }
  }, [])

  return { ...state, sendMessage, abort }
}
