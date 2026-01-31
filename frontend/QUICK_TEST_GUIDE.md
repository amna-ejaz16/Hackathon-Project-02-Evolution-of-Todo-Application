# Quick Test Guide - Authentication Fix Verification

## Prerequisites
- Backend running on `http://localhost:8000`
- Frontend running on `http://localhost:3000`
- Neon PostgreSQL database connected
- All environment variables configured

## Test Checklist

### 1. Clear Browser State (CRITICAL)
```
1. Open DevTools (F12)
2. Go to Application tab
3. Click "Storage" > "Clear site data"
4. Close and reopen browser
```

### 2. Test Signup Flow (2 minutes)
```
Step 1: Navigate to http://localhost:3000
Expected: Redirected to /signup page

Step 2: Fill in signup form
- Email: test@example.com
- Password: password123
- Confirm Password: password123

Step 3: Click "Create Account"
Expected: Redirected to /signin page (NOT dashboard)

Result: ✅ PASS / ❌ FAIL
```

### 3. Test Signin Flow (2 minutes)
```
Step 1: Fill in signin form
- Email: test@example.com
- Password: password123

Step 2: Click "Sign In"
Expected: Redirected to /dashboard

Step 3: Wait 3 seconds
Expected: Dashboard STAYS OPEN (no redirect back to signin)

Step 4: Check browser console
Expected: See these logs:
  - "Dashboard - Session state: { session: {...}, isPending: false }"
  - "Dashboard: Session confirmed, loading tasks"
  - "getToken response status: 200"

Result: ✅ PASS / ❌ FAIL
```

### 4. Test Task Operations (3 minutes)
```
Step 1: Create a task
- Title: "Test Task"
- Priority: High
- Click "Create Task"

Expected: Task appears in the list

Step 2: Toggle task completion
- Click checkbox next to task

Expected: Task marked as complete (strikethrough)

Step 3: Edit task
- Click edit icon
- Change title to "Updated Task"
- Click "Save Changes"

Expected: Task title updated

Step 4: Delete task
- Click delete icon
- Confirm deletion

Expected: Task removed from list

Result: ✅ PASS / ❌ FAIL
```

### 5. Test Signout (1 minute)
```
Step 1: Click "Sign Out" button

Expected: Redirected to /signin page

Step 2: Try to access /dashboard directly
- Navigate to http://localhost:3000/dashboard

Expected: Redirected to /signin (because not authenticated)

Result: ✅ PASS / ❌ FAIL
```

## Common Issues & Solutions

### Issue: "Session expired" error appears immediately
**Cause**: Better Auth session not persisting
**Debug**:
1. Check browser cookies (DevTools > Application > Cookies)
2. Should see `better-auth.session_token`
3. If missing, check BETTER_AUTH_SECRET matches between frontend and backend

**Fix**: Ensure `.env.local` has correct `BETTER_AUTH_SECRET`

---

### Issue: Dashboard shows "Authentication required" message
**Cause**: `getToken()` returning null
**Debug**:
1. Open browser console
2. Look for "getToken: No active session" message
3. Check if session cookie exists

**Fix**: Sign out and sign in again (clear cookies if needed)

---

### Issue: Backend returns 401 on all requests
**Cause**: JWT signature mismatch
**Debug**:
1. Check backend logs for "Invalid token" messages
2. Verify BETTER_AUTH_SECRET in backend `.env`
3. Ensure it matches frontend `.env.local`

**Fix**: Sync BETTER_AUTH_SECRET between frontend and backend

---

### Issue: Redirect loop still occurs
**Cause**: `hasAttemptedLoad` ref not working
**Debug**:
1. Open browser console
2. Look for multiple "Dashboard: Session confirmed" messages
3. If you see more than one, the ref guard failed

**Fix**: Check that React.StrictMode is not triggering double renders in development

---

### Issue: Tasks don't load (empty dashboard)
**Cause**: Backend API not running or database empty
**Debug**:
1. Check if backend is running: `curl http://localhost:8000/health`
2. Check browser Network tab for 500 errors
3. Check backend logs for errors

**Fix**: Start backend or check database connection

---

## Success Criteria

All tests must pass:
- ✅ Root redirects to signup
- ✅ Signup redirects to signin
- ✅ Signin redirects to dashboard
- ✅ Dashboard stays open (no redirect loop)
- ✅ Tasks can be created, edited, deleted, toggled
- ✅ Signout works and prevents dashboard access

## Timing Expectations

- **Signup**: < 2 seconds
- **Signin**: < 2 seconds
- **Dashboard load**: < 3 seconds (includes task fetch)
- **Task operations**: < 1 second each

If any operation takes longer, check:
- Network latency
- Neon database cold start (can take 5-10 seconds)
- Backend API performance

## Next Steps After Testing

### If ALL tests pass:
1. Test with different browsers (Chrome, Firefox, Edge)
2. Test with multiple users
3. Test session expiration (wait 24 hours or manually expire JWT)
4. Consider this fix complete ✅

### If ANY test fails:
1. Note which test failed
2. Check browser console for errors
3. Check backend logs
4. Review AUTHENTICATION_FIX_SUMMARY.md for debugging steps
5. Report issue with specific error messages

## Browser Console Commands for Debugging

### Check if session exists
```javascript
// In browser console:
fetch('http://localhost:3000/api/auth/session', {
  credentials: 'include'
}).then(r => r.json()).then(console.log)
```

Expected output: `{ session: { user: {...} }, user: {...} }`

### Check if token can be retrieved
```javascript
// In browser console:
fetch('http://localhost:3000/api/auth/token', {
  credentials: 'include'
}).then(r => r.json()).then(console.log)
```

Expected output: `{ token: "eyJ..." }`

### Check if backend accepts token
```javascript
// First get token, then test backend
fetch('http://localhost:3000/api/auth/token', {
  credentials: 'include'
})
.then(r => r.json())
.then(data => {
  return fetch('http://localhost:8000/api/tasks', {
    headers: {
      'Authorization': `Bearer ${data.token}`
    }
  });
})
.then(r => r.json())
.then(console.log)
```

Expected output: `{ tasks: [...], total: N }`

## Performance Benchmarks

Expected metrics (measure with DevTools Network tab):

| Operation | Time | Requests | Notes |
|-----------|------|----------|-------|
| Initial page load | < 1s | 3-5 | HTML, CSS, JS bundles |
| Session check | < 200ms | 1 | /api/auth/session |
| Token fetch | < 200ms | 1 | /api/auth/token |
| Tasks fetch | < 500ms | 1 | /api/tasks (depends on DB) |
| Create task | < 300ms | 1 | POST /api/tasks |
| Update task | < 300ms | 1 | PATCH /api/tasks/:id |
| Delete task | < 300ms | 1 | DELETE /api/tasks/:id |

If Neon database is in cold start, first request may take 5-10 seconds. Subsequent requests should be fast.
