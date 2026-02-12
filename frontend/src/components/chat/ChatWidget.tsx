'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence, PanInfo } from 'framer-motion'
import { api } from '@/lib/api'
import { logError, extractErrorDetails } from '@/lib/errorLogger'
import ChatHeader from './ChatHeader'
import ChatMessages from './ChatMessages'
import ChatInput from './ChatInput'
import QuickActionPills from './QuickActionPills'

interface ChatWidgetProps {
  onTaskChange: () => void
}

interface Message {
  id: number | string
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

interface ChatApiResponse {
  response: string
  conversation_id: number
  action?: string | null
  task_id?: number | null
}

interface HistoryMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  metadata?: Record<string, unknown> | null
  created_at: string
}

interface HistoryResponse {
  messages: HistoryMessage[]
  conversation_id: number | null
  total: number
}

const WELCOME_MESSAGE: Message = {
  id: 'welcome',
  role: 'assistant',
  content: "Hi! I'm your Task Manager Assistant. I can help you create, list, complete, update, and delete tasks. Try typing 'Show all my tasks' or use the quick actions below!",
  created_at: new Date().toISOString(),
}

// Error message templates
const ERROR_MESSAGES = {
  SERVICE_UNAVAILABLE: "I'm having trouble connecting right now. Please try again in a moment.",
  NETWORK_ERROR: "Connection lost. Please check your internet and try again.",
  SESSION_EXPIRED: "Session expired, please refresh the page.",
  GENERIC: "Sorry, something went wrong. Please try again.",
} as const

export default function ChatWidget({ onTaskChange }: ChatWidgetProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [isSending, setIsSending] = useState(false)
  const [conversationId, setConversationId] = useState<number | null>(null)
  const [historyLoaded, setHistoryLoaded] = useState(false)

  // Load chat history when panel opens for the first time
  useEffect(() => {
    if (isOpen && !historyLoaded) {
      loadChatHistory()
    }
  }, [isOpen, historyLoaded])

  // Reset chat state when panel closes (FR-026: fresh session on reopen)
  useEffect(() => {
    if (!isOpen) {
      setMessages([])
      setHistoryLoaded(true)  // Prevent reloading history on next open
      setConversationId(null)
    }
  }, [isOpen])

  const loadChatHistory = async () => {
    try {
      const data = await api.get<HistoryResponse>('/api/chat/history')

      if (data.messages && data.messages.length > 0) {
        const formattedMessages: Message[] = data.messages.map((msg) => ({
          id: msg.id,
          role: msg.role,
          content: msg.content,
          created_at: msg.created_at,
        }))
        setMessages(formattedMessages)
        setConversationId(data.conversation_id)
      } else {
        // No history, show welcome message
        setMessages([WELCOME_MESSAGE])
      }

      setHistoryLoaded(true)
    } catch (error) {
      // Log error with full details
      logError(error, {
        action: 'loadChatHistory',
        timestamp: new Date().toISOString(),
      })
      // On error, show welcome message
      setMessages([WELCOME_MESSAGE])
      setHistoryLoaded(true)
    }
  }

  const handleSendMessage = async (message: string) => {
    // Validate input
    if (!message || message.trim().length === 0) {
      logError(new Error('Empty message'), {
        action: 'sendMessage',
        component: 'ChatWidget',
        reason: 'empty_message',
        timestamp: new Date().toISOString(),
      })
      return
    }

    // Ensure chat is open (UI stability - prevent closing on error)
    if (!isOpen) {
      setIsOpen(true)
    }

    // Create temp user message
    const tempUserMessage: Message = {
      id: Date.now(),
      role: 'user',
      content: message,
      created_at: new Date().toISOString(),
    }

    // Add user message to UI
    try {
      setMessages((prev) => [...prev, tempUserMessage])
    } catch (e) {
      console.warn('Failed to add user message to state', e)
    }

    setIsSending(true)

    try {
      const data = await api.post<ChatApiResponse>('/api/chat', { message })

      // Validate API response
      if (!data || typeof data !== 'object') {
        throw new Error('Invalid API response format')
      }

      // Safely append assistant response
      const assistantMessage: Message = {
        id: Date.now() + 1,
        role: 'assistant',
        content: data.response || 'No response received',
        created_at: new Date().toISOString(),
      }

      try {
        setMessages((prev) => [...prev, assistantMessage])
      } catch (e) {
        console.warn('Failed to add assistant message to state', e)
      }

      // Update conversation ID safely
      if (data.conversation_id && typeof data.conversation_id === 'number') {
        try {
          setConversationId(data.conversation_id)
        } catch (e) {
          console.warn('Failed to update conversation ID', e)
        }
      }

      // If action affects tasks, trigger refresh
      // Validate action is a recognized type
      if (
        data.action &&
        typeof data.action === 'string' &&
        [
          'task_created',
          'task_updated',
          'task_completed',
          'task_uncompleted',
          'task_deleted',
        ].includes(data.action)
      ) {
        try {
          onTaskChange()
        } catch (e) {
          console.warn('Failed to trigger task change', e)
        }
      }
    } catch (error) {
      // Ensure error doesn't prevent UI from rendering
      try {
        // Log error with full details using error utility
        const errorDetails = logError(error, {
          action: 'sendMessage',
          conversationId,
          timestamp: new Date().toISOString(),
        })

        let errorContent: string = ERROR_MESSAGES.GENERIC
        let shouldSuggestRefresh = false

        // Determine error type and set appropriate message
        const status = errorDetails?.status
        const errorType = errorDetails?.type

        if (status === 503) {
          // Service unavailable - suggest retry
          errorContent = ERROR_MESSAGES.SERVICE_UNAVAILABLE
        } else if (status === 401 || status === 403) {
          // Session expired or unauthorized - suggest refresh
          errorContent = ERROR_MESSAGES.SESSION_EXPIRED
          shouldSuggestRefresh = true
        } else if (
          status === 500 ||
          status === 502 ||
          status === 504
        ) {
          // Server errors - suggest retry
          errorContent = "Server error. Please try again in a moment."
        } else if (
          errorType === 'NetworkError' ||
          errorType === 'TypeError' ||
          errorDetails?.code === 'ERR_NETWORK'
        ) {
          // Network connectivity issue
          errorContent = ERROR_MESSAGES.NETWORK_ERROR
        }

        // Append error message with optional refresh suggestion
        const errorMessage: Message = {
          id: Date.now() + 1,
          role: 'assistant',
          content: shouldSuggestRefresh
            ? `${errorContent}\n\nYou can refresh the page or try again later.`
            : errorContent,
          created_at: new Date().toISOString(),
        }

        // Safely append error message
        setMessages((prev) => {
          // Prevent duplicates in case of multiple error handling
          const isDuplicate = prev.some((m) => m.id === errorMessage.id)
          return isDuplicate ? prev : [...prev, errorMessage]
        })
      } catch (e) {
        // Last resort: if error handling itself fails, just log it
        console.error('Failed to handle chat error', e)

        // Still try to add a generic error message
        try {
          setMessages((prev) => [
            ...prev,
            {
              id: Date.now() + 1,
              role: 'assistant',
              content: ERROR_MESSAGES.GENERIC,
              created_at: new Date().toISOString(),
            },
          ])
        } catch (innerE) {
          console.error('Failed to add fallback error message', innerE)
        }
      }
    } finally {
      setIsSending(false)
    }
  }

  const handlePillClick = (message: string) => {
    if (!isSending) {
      handleSendMessage(message)
    }
  }

  const handleDragEnd = (_event: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
    // Close panel if dragged down significantly
    if (info.velocity.y > 500 || info.offset.y > 100) {
      setIsOpen(false)
    }
  }

  return (
    <>
      {/* FAB Button */}
      <AnimatePresence>
        {!isOpen && (
          <motion.button
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            exit={{ scale: 0 }}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setIsOpen(true)}
            className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 shadow-lg shadow-purple-500/40 flex items-center justify-center text-2xl"
            aria-label="Open chat assistant"
          >
            💬
          </motion.button>
        )}
      </AnimatePresence>

      {/* Chat Panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            key="chat-panel"
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.3 }}
            className="fixed z-50 bg-gray-900/90 backdrop-blur-xl border border-purple-500/20 shadow-xl shadow-purple-500/20 bottom-0 inset-x-0 h-[85vh] rounded-t-2xl md:bottom-6 md:right-6 md:left-auto md:inset-x-auto md:w-[380px] md:h-[560px] md:max-h-[560px] md:rounded-2xl"
          >
            <div className="flex flex-col h-full overflow-hidden">
              {/* Header with drag capability for mobile */}
              <motion.div
                drag="y"
                dragConstraints={{ top: 0, bottom: 0 }}
                dragElastic={0.2}
                onDragEnd={handleDragEnd}
                className="md:cursor-default"
              >
                <ChatHeader onClose={() => setIsOpen(false)} />
              </motion.div>

              {/* Messages */}
              <ChatMessages messages={messages} isLoading={isSending} />

              {/* Quick Action Pills */}
              <QuickActionPills onPillClick={handlePillClick} disabled={isSending} />

              {/* Input */}
              <ChatInput onSend={handleSendMessage} disabled={isSending} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}
