/**
 * Unified chat types to prevent TypeScript conflicts
 * This is the single source of truth for all chat-related interfaces
 */

/**
 * Core Message interface used throughout the chat system
 * id: Can be number (from backend) or string (temporary client-side IDs)
 * role: Either user message or assistant response
 * content: The actual message text
 * created_at: ISO 8601 timestamp
 */
export interface Message {
  id: number | string
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

/**
 * API response from chat endpoint
 */
export interface ChatApiResponse {
  response: string
  conversation_id: number
  action?: string | null
  task_id?: number | null
}

/**
 * Message from chat history (from backend)
 */
export interface HistoryMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  metadata?: Record<string, unknown> | null
  created_at: string
}

/**
 * Chat history response from backend
 */
export interface HistoryResponse {
  messages: HistoryMessage[]
  conversation_id: number | null
  total: number
}
