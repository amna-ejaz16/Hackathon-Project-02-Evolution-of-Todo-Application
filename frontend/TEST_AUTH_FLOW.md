# Authentication Flow Test Plan

## Expected Flow

### 1. First Visit (New User)
- User opens app at `/` (root)
- **EXPECTED**: Redirected to `/signup`
- **REASON**: Default landing page should be signup for new users

### 2. Signup Flow
- User fills out signup form:
  - Name (optional)
  - Email (required, validated)
  - Password (minimum 8 characters)
  - Confirm Password (must match)
- User submits form
- **EXPECTED**: Better Auth creates user account
- **EXPECTED**: Redirected to `/signin` (NOT dashboard)
- **REASON**: User must explicitly sign in after creating account

### 3. Signin Flow
- User fills out signin form:
  - Email
  - Password
- User submits form
- **EXPECTED**: Better Auth creates session and sets session cookie
- **EXPECTED**: Redirected to `/dashboard`

### 4. Dashboard Loading Sequence
This is the critical part where the redirect loop was occurring.

**Step-by-step expected behavior:**

1. **Dashboard page loads**
   - `useSession()` hook starts with `isPending=true`, `session=undefined`
   - Dashboard shows loading spinner
   - **NO API CALLS YET** (prevent race condition)

2. **Session loads**
   - Better Auth validates session cookie
   - `isPending=false`, `session={user: {...}}`
   - Dashboard detects session is ready

3. **Token acquisition**
   - `getToken()` is called
   - First checks if session exists using `getSession()`
   - If session exists, fetches JWT from `/api/auth/token`
   - Returns JWT token string

4. **Task fetching**
   - `fetchTasks()` is called (only once, controlled by `hasAttemptedLoad` ref)
   - `apiFetch()` calls `getToken()` to get JWT
   - JWT is attached to request: `Authorization: Bearer <token>`
   - Backend receives request, verifies JWT, returns user's tasks

5. **Dashboard displays tasks**
   - Tasks are rendered
   - User can create, edit, delete, toggle completion

### 5. Session Expiration Handling
- If JWT expires or is invalid:
  - Backend returns 401 Unauthorized
  - `apiFetch()` throws `ApiError` with `shouldRedirect=true`
  - Dashboard catches error and redirects to `/signin`
  - User must sign in again

### 6. Manual Navigation
- **User goes to `/` while authenticated**: Redirected to `/signup` (then to `/dashboard` if session exists)
- **User goes to `/signin` while authenticated**: Can still sign in (no redirect)
- **User goes to `/dashboard` while NOT authenticated**: Redirected to `/signin`

## Critical Bug Fixes Applied

### 1. Root Page Redirect (page.tsx)
**Before**: `redirect("/dashboard")`
**After**: `redirect("/signup")`
**Reason**: App should open on signup page, not signin

### 2. API 401 Redirect (api.ts)
**Before**: Automatically called `window.location.href = "/signin"`
**After**: Only throws error, lets component decide
**Reason**: Prevents redirect loop when dashboard is still loading

### 3. Dashboard Task Loading (dashboard/page.tsx)
**Before**: Fetched tasks on every `session` change
**After**: Only fetches once using `hasAttemptedLoad` ref
**Reason**: Prevents multiple API calls and redirect loops

### 4. getToken() Session Check (auth-client.ts)
**Before**: Directly called `/api/auth/token` without checking session
**After**: First checks if session exists using `getSession()`
**Reason**: Prevents unnecessary token requests when not authenticated

## Testing Steps

### Manual Testing

1. **Clear all cookies and browser storage**
   - Open DevTools > Application > Storage > Clear Site Data

2. **Test Signup**
   - Navigate to `http://localhost:3000`
   - Should see signup page
   - Create account with:
     - Email: test@example.com
     - Password: testpassword123
   - Submit form
   - **VERIFY**: Redirected to signin page

3. **Test Signin**
   - Fill in credentials
   - Submit form
   - **VERIFY**: Redirected to dashboard
   - **VERIFY**: Dashboard shows loading, then tasks
   - **VERIFY**: No redirect loop (dashboard stays open)

4. **Test Task Operations**
   - Create a new task
   - **VERIFY**: Task appears in list
   - Edit the task
   - **VERIFY**: Changes are saved
   - Toggle completion
   - **VERIFY**: Task marked as complete
   - Delete task
   - **VERIFY**: Task is removed

5. **Test Signout**
   - Click "Sign Out" button
   - **VERIFY**: Redirected to signin page
   - **VERIFY**: Cannot access dashboard without signing in

6. **Test Direct Navigation**
   - While signed in, navigate to `http://localhost:3000/`
   - **VERIFY**: Eventually lands on dashboard (not stuck in loop)
   - Sign out, then navigate to `http://localhost:3000/dashboard`
   - **VERIFY**: Redirected to signin page

### Automated Testing (Future)

```typescript
// Example E2E test with Playwright
test('authentication flow works correctly', async ({ page }) => {
  // 1. Root redirects to signup
  await page.goto('http://localhost:3000');
  await expect(page).toHaveURL(/\/signup/);

  // 2. Signup redirects to signin
  await page.fill('[name="email"]', 'test@example.com');
  await page.fill('[name="password"]', 'testpassword123');
  await page.fill('[name="confirmPassword"]', 'testpassword123');
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(/\/signin/);

  // 3. Signin redirects to dashboard
  await page.fill('[name="email"]', 'test@example.com');
  await page.fill('[name="password"]', 'testpassword123');
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(/\/dashboard/);

  // 4. Dashboard loads without redirect loop
  await page.waitForSelector('h1:has-text("Todo Dashboard")');
  await expect(page).toHaveURL(/\/dashboard/);
});
```

## Debugging

### Console Logs to Check

When loading dashboard, you should see:
```
Dashboard - Session state: { session: undefined, isPending: true, sessionError: undefined }
Dashboard - Session state: { session: { user: {...} }, isPending: false, sessionError: undefined }
Dashboard: Session confirmed, loading tasks
getToken: response status: 200
getToken: response data: { token: "eyJ..." }
```

### Common Issues

**Issue**: Dashboard shows "Authentication required" error
**Cause**: `getToken()` is returning null
**Fix**: Check browser cookies - should have `better-auth.session_token`

**Issue**: Backend returns 401
**Cause**: JWT signature mismatch
**Fix**: Ensure `BETTER_AUTH_SECRET` matches between frontend and backend

**Issue**: Redirect loop on dashboard
**Cause**: `fetchTasks()` is being called multiple times
**Fix**: Check `hasAttemptedLoad` ref is working correctly

**Issue**: Token endpoint returns 403
**Cause**: No session cookie sent
**Fix**: Ensure `credentials: "include"` in fetch options
