# Error Logger - Quick Reference Guide

## What Was Fixed

**Problem**: Chatbot errors were logged as empty objects `{}`, preventing debugging
**Solution**: Complete error logger rewrite with comprehensive error extraction and handling

## Key Improvements

### 1. Error Extraction

| Error Type | Before | After |
|-----------|--------|-------|
| API errors | ❌ Sometimes missed | ✅ Always extracted from response.data |
| Network errors | ❌ Partial info | ✅ Full details with URL |
| Response objects | ❌ Not handled | ✅ Properly detected and extracted |
| Plain objects | ❌ Often empty `{}` | ✅ Searches multiple property names |
| Error chains | ❌ No support | ✅ Captures Error.cause |

### 2. Error Information Captured

```javascript
// Before: Often {} or minimal info
console.error(formatted)

// After: Complete error information
{
  '🔴 Error': {
    message: 'Meaningful error description',
    type: 'Error type',
    httpStatus: 500,           // If HTTP error
    statusText: 'Error text',  // If HTTP error
    requestUrl: 'URL',         // If available
    errorCode: 'CODE'          // If available
  },
  '📋 Context': {
    action: 'what was happening',
    component: 'which component',
    timestamp: 'when it happened'
  },
  '📚 Stack Trace': 'where in code',
  '🔍 Raw Error': { /* original error */ }
}
```

### 3. Error Logging Safety

| Scenario | Before | After |
|----------|--------|-------|
| Circular refs | ❌ Infinite loop | ✅ Safe limit |
| Logger crash | ❌ Silent failure | ✅ Try-catch with fallback |
| Unknown errors | ❌ Often `{}` | ✅ Always meaningful message |
| Large objects | ❌ Performance issues | ✅ Truncated safely |

## Usage Examples

### Basic Usage (Unchanged)

```typescript
import { logError } from '@/lib/errorLogger'

try {
  const data = await api.post('/api/chat', { message })
} catch (error) {
  logError(error) // Simple logging
}
```

### With Context (Recommended)

```typescript
import { logError } from '@/lib/errorLogger'

try {
  const data = await api.post('/api/chat', { message })
} catch (error) {
  const details = logError(error, {
    action: 'sendMessage',
    component: 'ChatWidget',
    conversationId: id,
    timestamp: new Date().toISOString()
  })
}
```

### Programmatic Use

```typescript
import { logError } from '@/lib/errorLogger'

try {
  const data = await api.post('/api/chat', { message })
} catch (error) {
  const details = logError(error, { action: 'sendMessage' })

  // Access extracted error information
  if (details.status === 401) {
    // Session expired
  } else if (details.type === 'NetworkError') {
    // Network issue
  } else if (details.message) {
    // Use error message
    showToast(details.message)
  }
}
```

## Error Detection Capability

### Successfully Extracts From:

✅ `Error` objects
```javascript
throw new Error('Something went wrong')
```

✅ API errors (Axios)
```javascript
{
  response: {
    status: 500,
    data: { message: 'Server error' }
  }
}
```

✅ Fetch Response objects
```javascript
new Response(null, { status: 404, statusText: 'Not Found' })
```

✅ Network errors
```javascript
{
  request: { url: 'http://api.example.com' },
  message: 'Network timeout'
}
```

✅ Plain objects
```javascript
{ message: 'Error message', code: 'ERR_001' }
```

✅ Error chains
```javascript
new Error('Inner error', { cause: new Error('Outer error') })
```

✅ Strings
```javascript
'Simple string error'
```

✅ Edge cases
```javascript
null, undefined, 404, true, false
```

## Console Output Examples

### Scenario 1: API Error
```javascript
🚨 Error Logged
▶ {
  🔴 Error: {
    message: "Resource not found",
    type: "APIError",
    httpStatus: 404
  }
  📋 Context: { action: "loadChatHistory" }
  📚 Stack Trace: "Error at ChatWidget.tsx:94"
}
```

### Scenario 2: Network Error
```javascript
🚨 Error Logged
▶ {
  🔴 Error: {
    message: "Network request failed",
    type: "NetworkError",
    requestUrl: "http://localhost:8000/api/chat"
  }
  📋 Context: { action: "sendMessage" }
}
```

### Scenario 3: Unknown Error
```javascript
🚨 Error Logged
▶ {
  🔴 Error: {
    message: "Unknown error occurred",
    type: "object",
    details: "{message: 'Custom error'}"
  }
  🔍 Raw Error: { message: "Custom error" }
}
```

## Testing the Fix

### Run Tests
```bash
npm test src/lib/errorLogger.test.ts
```

### Manual Testing
```typescript
import { logError, extractErrorDetails } from '@/lib/errorLogger'

// Test 1: Standard Error
logError(new Error('Test error'))

// Test 2: API Error
logError({
  response: {
    status: 500,
    data: { message: 'Server error' }
  }
})

// Test 3: Empty object (should NOT show {})
logError({})

// Test 4: Network error
logError(new TypeError('Failed to fetch'))
```

## Verification Checklist

- ✅ No more `{}` in console
- ✅ All errors have meaningful messages
- ✅ Status codes are captured (for HTTP errors)
- ✅ Stack traces are shown
- ✅ Context information is logged
- ✅ TypeScript compiles without errors
- ✅ Works in development and production
- ✅ No performance degradation

## Files Modified

1. **`frontend/src/lib/errorLogger.ts`** (Main fix)
   - Enhanced `extractErrorDetails()` function
   - Improved `formatErrorForLogging()` function
   - New `safeStringify()` helper
   - Robust `logError()` with error handling

2. **`frontend/src/lib/errorLogger.test.ts`** (New)
   - Comprehensive test suite
   - Tests for all error types
   - Edge case coverage

## Key Functions

### `extractErrorDetails(error: unknown): ErrorDetails`
Safely extracts error information from any error type and returns:
```typescript
{
  message: string        // Always a meaningful message
  type: string          // Error type (Error, APIError, etc.)
  status?: number       // HTTP status if available
  statusText?: string   // HTTP status text
  code?: string         // Error code if available
  stack?: string        // Stack trace if available
  url?: string          // URL if available
  raw?: unknown         // Original error object
  details?: string      // Additional details if needed
}
```

### `formatErrorForLogging(details, context?): object`
Formats error details for console display with sections:
- `🔴 Error`: Main error info
- `📋 Context`: Request context
- `📚 Stack Trace`: First 5 frames
- `🔍 Raw Error`: Original object

### `logError(error, context?): ErrorDetails`
Main logging function that:
1. Extracts error details
2. Formats for display
3. Logs to console
4. Returns `ErrorDetails` for programmatic use
5. Prevents logger crashes

### `safeStringify(obj, maxDepth?, currentDepth?): string`
Safely stringifies objects:
- Prevents circular references
- Handles special objects (Error, Response)
- Truncates large objects
- Safe from infinite loops

## Troubleshooting

**Q: Still seeing empty objects?**
- Refresh the page (clear browser cache)
- Check if you're using latest code
- Look for `🔍 Raw Error` section

**Q: Error logger throwing error?**
- Protected with try-catch
- Will log "ERROR LOGGER FAILED"
- Check browser console for original error

**Q: Not capturing certain errors?**
- Verify error structure
- Check for circular references
- Review test cases

## Next Steps

1. **Deploy the fix**: No code changes needed for existing error handling
2. **Monitor**: Check browser console for proper error logging
3. **Update error handling**: Optionally use returned `ErrorDetails` for UX improvements
4. **Add analytics**: Consider sending `ErrorDetails` to error tracking service

## Related Files

- `frontend/src/components/chat/ChatWidget.tsx` - Uses error logger
- `frontend/src/lib/api.ts` - API client that throws errors
- `docs/ERROR_LOGGER_FIX.md` - Complete technical documentation
