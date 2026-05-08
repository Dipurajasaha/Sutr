import { useEffect, useRef, useState } from 'react'
import axios from 'axios'
import { Send, Sparkles, AlertCircle } from 'lucide-react'
import { apiClient } from '../api/client'
import type { FileSystemItem } from './types'
import MarkdownBlock from './MarkdownBlock'

type ChatViewProps = {
  activeFile: FileSystemItem | null
  onCitationClick?: (startTime: number) => void
}

type SourceChunk = Record<string, unknown>

type ChatMessage = {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: SourceChunk[]
}

type ChatResponse = {
  answer: string
  sources?: SourceChunk[]
}

type ChatHistoryMessage = {
  role: 'human' | 'ai'
  content: string
}

type ChatHistoryResponse = {
  session_id: string
  messages: ChatHistoryMessage[]
}

const buildSessionStorageKey = (fileId: string) => `sutr_chat_session_${fileId}`

const createSessionId = () => `session_${Math.random().toString(36).substring(2, 11)}_${Date.now()}`

export default function ChatView({ activeFile, onCitationClick }: ChatViewProps) {
  const isFile = activeFile?.type === 'file'
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string>('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [sessionId, setSessionId] = useState('')

  useEffect(() => {
    if (!activeFile?.id) {
      setSessionId('')
      setMessages([])
      return
    }

    const storageKey = buildSessionStorageKey(activeFile.id)
    const existingSessionId = window.localStorage.getItem(storageKey)
    const nextSessionId = existingSessionId ?? createSessionId()

    if (!existingSessionId) {
      window.localStorage.setItem(storageKey, nextSessionId)
    }

    setSessionId(nextSessionId)
  }, [activeFile?.id])

  useEffect(() => {
    const loadHistory = async () => {
      if (!sessionId || !isFile) return

      try {
        const response = await apiClient.get<ChatHistoryResponse>(`/api/chat/history/${sessionId}`)
        const historyMessages: ChatMessage[] = response.data.messages.map((message, index) => ({
          id: `history_${sessionId}_${index}`,
          role: message.role === 'human' ? 'user' : 'assistant',
          content: message.content,
        }))
        setMessages(historyMessages)
      } catch (historyError) {
        console.error('Failed to load chat history:', historyError)
        setMessages([])
      }
    }

    void loadHistory()
  }, [sessionId, isFile])

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Helper to format seconds into MM:SS
  const formatTime = (seconds: number) => {
    if (!Number.isFinite(seconds) || isNaN(seconds)) return '00:00'
    const total = Math.floor(seconds)
    const m = Math.floor(total / 60)
    const s = total % 60
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!inputValue.trim() || !isFile || !activeFile || !sessionId) return

    // Add user message immediately
    const userMessage: ChatMessage = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content: inputValue,
    }
    setMessages((prev) => [...prev, userMessage])
    setInputValue('')
    setIsLoading(true)
    setError('')

    try {
      const response = await apiClient.post<ChatResponse>('/api/chat/query/', {
        session_id: sessionId,
        query: inputValue,
        file_id: activeFile.id,
      })

      const assistantMessage: ChatMessage = {
        id: `msg_${Date.now()}_ai`,
        role: 'assistant',
        content: response.data.answer,
        sources: response.data.sources,
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch (err) {
      const errorMessage =
        axios.isAxiosError(err) && err.response?.data?.detail
          ? typeof err.response.data.detail === 'string'
            ? err.response.data.detail
            : 'Failed to get response from AI'
          : err instanceof Error
            ? err.message
            : 'An error occurred while processing your message'

      setError(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex h-full flex-col bg-zinc-950">
      <div className="flex-1 overflow-y-auto px-6 py-6">
        {isFile ? (
          <div className="mx-auto flex max-w-4xl flex-col gap-4">
            {messages.length === 0 && (
              <div className="flex h-full items-center justify-center text-center">
                <div className="text-zinc-500">
                  <p>Start a conversation about this document</p>
                </div>
              </div>
            )}
            {messages.map((message) => {
              const isUser = message.role === 'user'
              return (
                <div key={message.id} className={`flex max-w-[85%] ${isUser ? 'ml-auto justify-end' : 'mr-auto justify-start'}`}>
                  <div
                    className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                      isUser ? 'bg-zinc-800 text-zinc-100' : 'border-l-2 border-purple-500/80 bg-zinc-950 text-zinc-300'
                    }`}
                  >
                    {!isUser ? (
                      <div className="mb-1 flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-purple-400">
                        <Sparkles className="h-3.5 w-3.5" />
                        AI
                      </div>
                    ) : null}
                    <MarkdownBlock
                      className="prose prose-invert max-w-none text-sm leading-relaxed"
                      content={message.content}
                    />
                      {/* Render citation buttons if assistant message has sources with start timestamps */}
                      {!isUser && message.sources && message.sources.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-2">
                          {message.sources.map((src, idx) => {
                            const start = src?.start ?? src?.start_time ?? src?.timestamp ?? null
                            if (start == null || typeof start !== 'number') return null
                            return (
                              <button
                                key={`${message.id}-src-${idx}`}
                                type="button"
                                className="bg-zinc-800 hover:bg-purple-600 text-xs px-2 py-1 rounded-full"
                                onClick={() => onCitationClick?.(start)}
                              >
                                Play citation {formatTime(start)}
                              </button>
                            )
                          })}
                        </div>
                      )}
                  </div>
                </div>
              )
            })}
            {isLoading && (
              <div className="flex max-w-[85%] justify-start">
                <div className="rounded-2xl border-l-2 border-purple-500/80 bg-zinc-950 px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="flex gap-1">
                      <div className="h-2 w-2 rounded-full bg-purple-400 animate-pulse" />
                      <div className="h-2 w-2 rounded-full bg-purple-400 animate-pulse animation-delay-100" />
                      <div className="h-2 w-2 rounded-full bg-purple-400 animate-pulse animation-delay-200" />
                    </div>
                    <span className="text-xs text-purple-400">AI is thinking...</span>
                  </div>
                </div>
              </div>
            )}
            {error && (
              <div className="mx-auto max-w-4xl">
                <div className="flex gap-3 rounded-xl border border-red-500/50 bg-red-500/10 p-4">
                  <AlertCircle className="h-5 w-5 shrink-0 text-red-400" />
                  <p className="text-sm text-red-300">{error}</p>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        ) : (
          <div className="flex h-full items-center justify-center text-zinc-500">
            Select a file to begin chatting.
          </div>
        )}
      </div>

      <div className="shrink-0 border-t border-zinc-800 bg-zinc-950 px-6 py-5">
        <div className="mx-auto max-w-4xl">
          <form onSubmit={handleSubmit} className="relative">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              disabled={!isFile || isLoading}
              placeholder="Ask a question about this document..."
              className="h-14 w-full rounded-full border border-zinc-700 bg-zinc-900 pl-5 pr-14 text-sm text-white outline-none placeholder:text-zinc-500 focus:ring-2 focus:ring-purple-500 disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={!isFile || isLoading || !inputValue.trim()}
              className="absolute right-2 top-1/2 flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full bg-purple-600 text-white disabled:opacity-50 hover:bg-purple-700 transition"
              aria-label="Send message"
            >
              <Send className="h-4 w-4" />
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
