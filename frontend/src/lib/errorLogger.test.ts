/**
 * Test suite for error logger functionality
 * Tests extraction and formatting of various error types
 */

import {
  extractErrorDetails,
  formatErrorForLogging,
  logError,
  ErrorDetails,
} from './errorLogger'

describe('errorLogger', () => {
  describe('extractErrorDetails', () => {
    it('should handle Error objects', () => {
      const error = new Error('Test error message')
      const details = extractErrorDetails(error)

      expect(details.message).toBe('Test error message')
      expect(details.type).toBe('Error')
      expect(details.stack).toBeDefined()
    })

    it('should handle TypeError', () => {
      const error = new TypeError('Cannot read properties')
      const details = extractErrorDetails(error)

      expect(details.message).toBe('Cannot read properties')
      expect(details.type).toBe('TypeError')
    })

    it('should handle strings', () => {
      const error = 'Simple string error'
      const details = extractErrorDetails(error)

      expect(details.message).toBe('Simple string error')
      expect(details.type).toBe('string')
    })

    it('should handle empty objects', () => {
      const error = {}
      const details = extractErrorDetails(error)

      expect(details.message).not.toBe('')
      expect(details.type).toBe('object')
    })

    it('should handle null', () => {
      const error = null
      const details = extractErrorDetails(error)

      expect(details.message).toBe('Null error')
      expect(details.type).toBe('null')
    })

    it('should handle undefined', () => {
      const error = undefined
      const details = extractErrorDetails(error)

      expect(details.message).toBe('Undefined error')
      expect(details.type).toBe('undefined')
    })

    it('should extract message from objects with message property', () => {
      const error = { message: 'Object with message' }
      const details = extractErrorDetails(error)

      expect(details.message).toBe('Object with message')
    })

    it('should extract API error details', () => {
      const error = {
        response: {
          status: 404,
          statusText: 'Not Found',
          data: { message: 'Resource not found' },
        },
      }
      const details = extractErrorDetails(error)

      expect(details.status).toBe(404)
      expect(details.statusText).toBe('Not Found')
      expect(details.message).toBe('Resource not found')
      expect(details.type).toBe('APIError')
    })

    it('should extract error from response data.error field', () => {
      const error = {
        response: {
          status: 500,
          statusText: 'Server Error',
          data: { error: 'Internal server error' },
        },
      }
      const details = extractErrorDetails(error)

      expect(details.message).toBe('Internal server error')
    })

    it('should extract error from response data.detail field', () => {
      const error = {
        response: {
          status: 422,
          statusText: 'Unprocessable Entity',
          data: { detail: 'Validation failed' },
        },
      }
      const details = extractErrorDetails(error)

      expect(details.message).toBe('Validation failed')
    })

    it('should handle network errors', () => {
      const error = {
        request: { url: 'http://api.example.com' },
        message: 'Network request failed',
      }
      const details = extractErrorDetails(error)

      expect(details.type).toBe('NetworkError')
      expect(details.message).toBe('Network request failed')
      expect(details.url).toBe('http://api.example.com')
    })

    it('should extract error code', () => {
      const error = {
        message: 'ECONNREFUSED',
        code: 'ECONNREFUSED',
      }
      const details = extractErrorDetails(error)

      expect(details.code).toBe('ECONNREFUSED')
    })

    it('should handle Response objects', () => {
      const response = new Response(JSON.stringify({ error: 'Bad Request' }), {
        status: 400,
        statusText: 'Bad Request',
      })
      const details = extractErrorDetails(response)

      expect(details.status).toBe(400)
      expect(details.statusText).toBe('Bad Request')
    })

    it('should search for error in common property names', () => {
      const error = {
        err: 'Error in err property',
      }
      const details = extractErrorDetails(error)

      expect(details.message).toBe('Error in err property')
    })

    it('should handle objects with name property', () => {
      const error = {
        name: 'CustomError',
        message: 'Custom error message',
      }
      const details = extractErrorDetails(error)

      expect(details.type).toBe('CustomError')
      expect(details.message).toBe('Custom error message')
    })

    it('should never return empty message', () => {
      const error = {}
      const details = extractErrorDetails(error)

      expect(details.message).toBeTruthy()
      expect(details.message).not.toBe('')
    })
  })

  describe('formatErrorForLogging', () => {
    it('should format error details with all properties', () => {
      const details: ErrorDetails = {
        message: 'Test error',
        type: 'Error',
        status: 500,
        statusText: 'Internal Server Error',
        code: 'ERR_500',
        stack: 'Error: Test\n  at line 1',
        url: 'http://api.example.com',
      }

      const formatted = formatErrorForLogging(details)

      expect(formatted['🔴 Error']).toBeDefined()
      expect(formatted['🔴 Error'].message).toBe('Test error')
      expect(formatted['🔴 Error'].type).toBe('Error')
      expect(formatted['🔴 Error'].httpStatus).toBe(500)
      expect(formatted['📚 Stack Trace']).toBeDefined()
    })

    it('should include context when provided', () => {
      const details: ErrorDetails = {
        message: 'Test error',
        type: 'Error',
      }
      const context = { component: 'ChatWidget', action: 'sendMessage' }

      const formatted = formatErrorForLogging(details, context)

      expect(formatted['📋 Context']).toEqual(context)
    })

    it('should include raw error when present', () => {
      const error = new Error('Original error')
      const details = extractErrorDetails(error)
      const formatted = formatErrorForLogging(details)

      expect(formatted['🔍 Raw Error']).toBeDefined()
    })

    it('should not include context when empty', () => {
      const details: ErrorDetails = {
        message: 'Test error',
        type: 'Error',
      }

      const formatted = formatErrorForLogging(details, {})

      expect(formatted['📋 Context']).toBeUndefined()
    })
  })

  describe('logError', () => {
    let consoleSpy: jest.SpyInstance

    beforeEach(() => {
      consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {})
      jest.spyOn(console, 'group').mockImplementation(() => {})
      jest.spyOn(console, 'groupEnd').mockImplementation(() => {})
    })

    afterEach(() => {
      consoleSpy.mockRestore()
      jest.restoreAllMocks()
    })

    it('should log error and return details', () => {
      const error = new Error('Test error')
      const details = logError(error)

      expect(details.message).toBe('Test error')
      expect(details.type).toBe('Error')
      expect(consoleSpy).toHaveBeenCalled()
    })

    it('should include context in logging', () => {
      const error = new Error('Test error')
      const context = { action: 'test' }
      const details = logError(error, context)

      expect(details).toBeDefined()
      expect(consoleSpy).toHaveBeenCalled()
    })

    it('should not crash on logging error', () => {
      const circularObj: any = { ref: null }
      circularObj.ref = circularObj

      expect(() => {
        logError(circularObj)
      }).not.toThrow()
    })

    it('should handle empty error objects', () => {
      const error = {}
      const details = logError(error)

      expect(details.message).toBeTruthy()
      expect(details.type).toBe('object')
    })

    it('should return ErrorDetails even on logging failure', () => {
      const error = new Error('Test')
      const details = logError(error)

      expect(details).toHaveProperty('message')
      expect(details).toHaveProperty('type')
    })
  })

  describe('edge cases', () => {
    it('should handle deeply nested errors', () => {
      const error = {
        response: {
          data: {
            errors: [{ message: 'Nested error' }],
          },
        },
      }
      const details = extractErrorDetails(error)

      expect(details).toBeDefined()
      expect(details.type).toBe('APIError')
    })

    it('should handle errors with special characters', () => {
      const error = 'Error: 🔴 Something went wrong'
      const details = extractErrorDetails(error)

      expect(details.message).toContain('🔴')
    })

    it('should handle very large error messages', () => {
      const longMessage = 'x'.repeat(10000)
      const error = new Error(longMessage)
      const details = extractErrorDetails(error)

      expect(details.message).toBe(longMessage)
    })

    it('should handle numbers as errors', () => {
      const error = 404
      const details = extractErrorDetails(error)

      expect(details.message).toBe('404')
      expect(details.type).toBe('number')
    })

    it('should handle booleans as errors', () => {
      const error = true
      const details = extractErrorDetails(error)

      expect(details.message).toBe('true')
      expect(details.type).toBe('boolean')
    })
  })
})
