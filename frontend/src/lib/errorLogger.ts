/**
 * Utility for safely extracting and logging errors of any type
 * Handles Error objects, API errors, strings, and unknown types
 */

export interface ErrorDetails {
  message: string
  type: string
  status?: number
  statusText?: string
  code?: string
  stack?: string
  url?: string
  cause?: unknown
  raw?: unknown
}

/**
 * Safely extract error information from any error type
 * Handles: Error, AxiosError, fetch Response, strings, objects, etc.
 */
export function extractErrorDetails(error: unknown): ErrorDetails {
  const details: ErrorDetails = {
    message: 'Unknown error occurred',
    type: typeof error,
    raw: error,
  }

  // Handle Error objects (including TypeError, ReferenceError, etc.)
  if (error instanceof Error) {
    details.message = error.message || 'Error with no message'
    details.type = error.constructor.name
    details.stack = error.stack
    details.code = (error as Record<string, unknown>).code as string | undefined
    details.cause = error.cause
    return details
  }

  // Handle objects with response property (Axios errors, custom API errors)
  if (error && typeof error === 'object') {
    const errorObj = error as Record<string, unknown>

    // Check for HTTP response status
    if ('response' in errorObj && errorObj.response) {
      const response = errorObj.response as Record<string, unknown>
      details.status = response.status as number | undefined
      details.statusText = response.statusText as string | undefined
      details.message = response.statusText || `HTTP ${response.status}`
      details.type = 'APIError'

      // Extract message from response data if available
      if ('data' in response && response.data) {
        const data = response.data as Record<string, unknown>
        if ('message' in data && typeof data.message === 'string') {
          details.message = data.message
        } else if ('error' in data && typeof data.error === 'string') {
          details.message = data.error
        }
      }
    }

    // Check for request property (network errors)
    if ('request' in errorObj && !details.status) {
      details.type = 'NetworkError'
      details.message = errorObj.message as string || 'Network request failed'
      details.url = (errorObj.request as Record<string, unknown>)?.url as string | undefined
    }

    // Check for message property
    if ('message' in errorObj && typeof errorObj.message === 'string') {
      details.message = errorObj.message
    }

    // Check for name property
    if ('name' in errorObj && typeof errorObj.name === 'string') {
      details.type = errorObj.name
    }

    // Check for code property (useful for specific errors)
    if ('code' in errorObj && typeof errorObj.code === 'string') {
      details.code = errorObj.code
    }
  }

  // Handle strings
  if (typeof error === 'string') {
    details.message = error
    details.type = 'string'
  }

  // Handle numbers, booleans, null, undefined
  if (typeof error === 'number' || typeof error === 'boolean') {
    details.message = String(error)
    details.type = typeof error
  }

  return details
}

/**
 * Format error details for console logging
 * Returns an object that displays well in browser DevTools
 * FIXED: Now handles empty/sparse error objects properly
 */
export function formatErrorForLogging(
  details: ErrorDetails,
  context?: Record<string, unknown>
) {
  // Build the error object with all available information
  const errorObj: Record<string, unknown> = {
    message: details.message || '(no message)',
    type: details.type || '(unknown)',
  }

  // Add HTTP details if available
  if (details.status) {
    errorObj.httpStatus = details.status
  }
  if (details.statusText) {
    errorObj.statusText = details.statusText
  }
  if (details.code) {
    errorObj.errorCode = details.code
  }
  if (details.url) {
    errorObj.requestUrl = details.url
  }

  const formatted: Record<string, unknown> = {
    '🔴 Error': errorObj,
  }

  // Add context if provided
  if (context && Object.keys(context).length > 0) {
    formatted['📋 Context'] = context
  }

  // Add stack trace if available
  if (details.stack) {
    formatted['📚 Stack Trace'] = details.stack
      .split('\n')
      .slice(0, 5) // First 5 stack frames
      .join('\n')
  }

  return formatted
}

/**
 * Unified error logger function
 * FIXED: Now logs complete error information even for sparse error objects
 * Usage: logError(error, { componentName: 'ChatWidget', action: 'sendMessage' })
 */
export function logError(
  error: unknown,
  context?: Record<string, unknown>
) {
  const details = extractErrorDetails(error)
  const formatted = formatErrorForLogging(details, context)

  // Log with error group for better organization in DevTools
  console.group('🚨 Error Logged')

  // Always log the formatted error object
  console.error(formatted)

  // Also log the raw error for debugging if it has properties
  if (error && typeof error === 'object') {
    const errorObj = error as Record<string, unknown>
    const keys = Object.keys(errorObj)
    if (keys.length > 0) {
      console.error('Raw error object:', error)
    }
  }

  console.groupEnd()

  // Also return details for programmatic use (e.g., error reporting services)
  return details
}

/**
 * Get a user-friendly error message
 * Useful for determining what to display to the user
 */
export function getUserFriendlyMessage(error: unknown): string {
  const details = extractErrorDetails(error)

  // Special handling for common HTTP errors
  if (details.status === 503) {
    return "Service temporarily unavailable. Please try again in a moment."
  }
  if (details.status === 401) {
    return "Session expired. Please refresh the page and try again."
  }
  if (details.status === 404) {
    return "The requested resource was not found."
  }
  if (details.status && details.status >= 500) {
    return "Server error. Please try again later."
  }
  if (details.status && details.status >= 400) {
    return `Error: ${details.message}`
  }

  // Check for network errors
  if (
    details.type === 'NetworkError' ||
    details.type === 'TypeError' ||
    (details.message && details.message.includes('fetch'))
  ) {
    return "Connection error. Please check your internet and try again."
  }

  // Default fallback
  return details.message || "Something went wrong. Please try again."
}
