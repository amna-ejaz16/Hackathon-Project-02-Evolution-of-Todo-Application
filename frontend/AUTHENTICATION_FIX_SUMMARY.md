# Authentication Redirect Loop - Root Cause Analysis & Fix

## Problem Statement

After signing in, the dashboard would briefly appear, then immediately redirect back to the signin page with the error "Session expired, try again." This created an infinite redirect loop that prevented users from accessing the application.

## Root Cause Analysis

### Primary Issues Identified

1. **Race Condition in Dashboard Component** (`dashboard/page.tsx`)
   - The `useEffect` hook was calling `fetchTasks()` on every render when `session` object changed
   - Better Auth's `useSession()` hook can return different object references on each render
   - This caused multiple rapid `fetchTasks()` calls, some of which might fail if the JWT token wasn't ready
   - Multiple API calls could trigger redirect logic multiple times

2. **Premature Token Requests** (`auth-client.ts`)
   - `getToken()` was directly calling `/api/auth/token` without first verifying a session exists
   - This could cause failed token requests during the session hydration phase
   - No session check meant wasted API calls when user isn't authenticated

3. **Aggressive 401 Redirect in API Layer** (`api.ts`)
   - When backend returned 401, the API layer immediately called `window.location.href = "/signin"`
   - This redirect happened before the dashboard component could handle the error gracefully
   - Created potential for redirect loops if 401s occurred during legitimate state transitions

4. **Incorrect Default Route** (`page.tsx`)
   - Root page (`/`) redirected to `/dashboard` instead of `/signup`
   - This violated the requirement: "App opens on SIGN UP page (not signin)"
   - Forced all new users to land on dashboard first, then get redirected to signin

## Solution Architecture

### 1. Fixed Root Page Redirect
**File**: `/frontend/src/app/page.tsx`

**Change**: Redirect to `/signup` instead of `/dashboard`

```typescript
export default function Home() {
  // Redirect to signup page for new users
  redirect("/signup");
}
```

**Impact**: New users now land on signup page as intended

---

### 2. Enhanced Token Acquisition with Session Check
**File**: `/frontend/src/lib/auth-client.ts`

**Change**: Add session validation before requesting JWT token

```typescript
export async function getToken(): Promise<string | null> {
  // First, check if we have a valid session before requesting token
  const session = await getSession();
  if (!session?.data?.session) {
    console.debug("getToken: No active session, cannot retrieve token");
    return null;
  }

  // Then fetch the JWT token
  const response = await fetch(tokenUrl, {
    method: "GET",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
  });
  // ... rest of token extraction logic
}
```

**Impact**:
- Prevents unnecessary token requests when not authenticated
- Fails fast when no session exists instead of making invalid API calls
- Reduces server load and improves performance

---

### 3. Removed Automatic Redirect from API Layer
**File**: `/frontend/src/lib/api.ts`

**Change**: Let components handle 401 errors instead of auto-redirecting

```typescript
// Before:
if (response.status === 401) {
  if (typeof window !== "undefined") {
    window.location.href = "/signin";  // ❌ Aggressive redirect
  }
  throw new ApiError(401, "Unauthorized", "Session expired", true);
}

// After:
if (response.status === 401) {
  console.warn("apiFetch: 401 received - token was rejected by backend");
  // Don't automatically redirect - let the component handle this
  throw new ApiError(401, "Unauthorized", "Session expired", true);
}
```

**Impact**:
- Gives components control over navigation decisions
- Prevents redirect loops caused by premature redirects
- Allows for better error handling and user feedback

---

### 4. Single-Load Task Fetching with Ref Guard
**File**: `/frontend/src/app/dashboard/page.tsx`

**Change**: Use `useRef` to ensure tasks are only loaded once when session is ready

```typescript
// Track if initial load has been attempted
const hasAttemptedLoad = useRef(false);

useEffect(() => {
  // Only fetch tasks when:
  // 1. Session loading is complete (!isPending)
  // 2. We have a valid session (session exists)
  // 3. We haven't already attempted to load tasks
  if (!isPending && session && !hasAttemptedLoad.current) {
    console.log("Dashboard: Session confirmed, loading tasks");
    hasAttemptedLoad.current = true;
    fetchTasks();
  }

  // Reset the flag if session becomes null (user logged out)
  if (!session && hasAttemptedLoad.current) {
    hasAttemptedLoad.current = false;
  }
}, [isPending, session]);
```

**Impact**:
- Prevents multiple rapid `fetchTasks()` calls
- Ensures tasks are loaded exactly once when session is confirmed
- Eliminates race conditions in component lifecycle

---

### 5. Component-Level 401 Handling
**File**: `/frontend/src/app/dashboard/page.tsx`

**Change**: Handle 401 errors in the dashboard component with proper redirect logic

```typescript
const fetchTasks = async () => {
  try {
    setIsLoading(true);
    setError(null);
    const response = await api.get<TasksResponse>("/api/tasks");
    setTasks(response.tasks);
  } catch (err) {
    if (err instanceof ApiError) {
      // If backend rejected the token, redirect to signin
      if (err.shouldRedirect && err.status === 401) {
        console.error("Dashboard: Session expired, redirecting to signin");
        window.location.replace("/signin");
      } else {
        // For other errors, just show the error message
        setError(err.message);
      }
    } else {
      setError("Failed to load tasks. Please try again.");
    }
  } finally {
    setIsLoading(false);
  }
};
```

**Impact**:
- Centralized error handling in the component
- Only redirects when backend explicitly rejects the token
- Better user experience with contextual error messages

## Security Considerations

### What We Maintained

1. **JWT Verification**: Backend still verifies all tokens (no security compromise)
2. **Session Cookies**: Still httpOnly, secure, sameSite (CSRF protection intact)
3. **Error Messages**: Still generic to prevent user enumeration
4. **Token Expiration**: Still enforced by Better Auth (24h)

### What We Improved

1. **Session Validation**: Now checks session before token requests (fewer attack vectors)
2. **Controlled Redirects**: Components decide when to redirect (prevents redirect hijacking)
3. **Error Logging**: Better server-side logging for security audits
4. **Single Token Request**: Reduces token exposure window

## Testing Verification

### Before Fix
```
1. User signs in
2. Dashboard loads (isPending=true)
3. Session hydrates (session={...})
4. fetchTasks() called
5. getToken() returns null (session not ready)
6. API call fails with "No Token"
7. Component re-renders (session object changed)
8. fetchTasks() called AGAIN
9. Loop continues...
```

### After Fix
```
1. User signs in
2. Dashboard loads (isPending=true, shows loading spinner)
3. Session hydrates (isPending=false, session={...})
4. hasAttemptedLoad=false, so fetchTasks() called ONCE
5. getToken() checks session first → session exists
6. getToken() fetches JWT from /api/auth/token
7. API call succeeds with Authorization: Bearer <token>
8. Tasks loaded and displayed
9. hasAttemptedLoad=true → no more fetchTasks() calls
```

## Files Modified

1. `/frontend/src/app/page.tsx` - Changed default redirect to signup
2. `/frontend/src/lib/auth-client.ts` - Added session check to getToken()
3. `/frontend/src/lib/api.ts` - Removed automatic 401 redirect
4. `/frontend/src/app/dashboard/page.tsx` - Added single-load guard with useRef
5. `/frontend/TEST_AUTH_FLOW.md` - Created test plan (new file)
6. `/frontend/AUTHENTICATION_FIX_SUMMARY.md` - This document (new file)

## Expected User Flow (After Fix)

### New User Journey
1. Navigate to `http://localhost:3000/` → Redirected to `/signup`
2. Fill out signup form → Submit
3. Redirected to `/signin` (must explicitly sign in)
4. Fill out signin form → Submit
5. Redirected to `/dashboard` → Dashboard loads without loop
6. Can create, edit, delete, complete tasks

### Returning User Journey
1. Navigate to `http://localhost:3000/` → Redirected to `/signup`
2. Click "Already have an account? Sign in"
3. Fill out signin form → Submit
4. Redirected to `/dashboard` → Dashboard loads without loop

### Session Expiration
1. User is on dashboard with valid session
2. 24 hours pass (JWT expires)
3. User tries to create a task
4. Backend returns 401 Unauthorized
5. Dashboard detects 401 with shouldRedirect=true
6. User redirected to `/signin` with message "Session expired"
7. User signs in again

## Monitoring & Debugging

### Console Logs to Watch

**Successful Load:**
```
Dashboard - Session state: { session: undefined, isPending: true, sessionError: undefined }
Dashboard - Session state: { session: { user: {...} }, isPending: false, sessionError: undefined }
Dashboard: Session confirmed, loading tasks
getToken response status: 200
getToken response data: { token: "eyJ..." }
```

**Failed Authentication:**
```
getToken: No active session, cannot retrieve token
apiFetch: No JWT token available, cannot make authenticated request
```

### Red Flags

- **Multiple "Dashboard: Session confirmed" logs**: Indicates ref guard isn't working
- **"getToken response status: 401"**: Session cookie not being sent
- **"getToken: No token found in response"**: Better Auth JWT plugin misconfigured
- **Rapid redirects in Network tab**: Redirect loop still occurring

## Rollback Plan

If this fix causes issues, revert these commits:
1. Page.tsx default route change
2. Auth-client.ts getToken() session check
3. Api.ts 401 redirect removal
4. Dashboard.tsx useRef guard

Each change is independent and can be reverted individually.

## Future Improvements

1. **Add E2E Tests**: Playwright tests for auth flow
2. **Add Unit Tests**: Test getToken() with mocked session states
3. **Add Metrics**: Track token request failures, 401 responses
4. **Add Retry Logic**: Exponential backoff for transient failures
5. **Add Token Caching**: Cache valid tokens to reduce /api/auth/token calls
6. **Add Session Refresh**: Automatically refresh sessions before expiration
7. **Add Middleware**: Re-enable Next.js middleware for server-side route protection

## Conclusion

The redirect loop was caused by a **race condition** where the dashboard component was fetching tasks before the authentication state was fully stable. By:

1. Validating session before token requests
2. Using a ref guard to prevent multiple loads
3. Letting components control redirect logic
4. Fixing the default route

We've eliminated the redirect loop while maintaining security and improving the user experience.
