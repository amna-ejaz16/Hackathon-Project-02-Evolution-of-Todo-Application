# Testing the Neon PostgreSQL Connection Fix

## Pre-Flight Checklist

Before testing, verify:

1. **Environment variables are set** (`.env.local`):
   ```bash
   cd frontend
   cat .env.local
   ```

   Should contain:
   ```
   BETTER_AUTH_SECRET=tTfFs2FiMXdhA7f483bq1aE8vIvkLRDWj58fNmMZSyI=
   BETTER_AUTH_URL=http://localhost:3000
   NEXT_PUBLIC_BETTER_AUTH_URL=http://localhost:3000
   NEXT_PUBLIC_API_URL=http://localhost:8000
   DATABASE_URL=postgresql://neondb_owner:npg_***@ep-muddy-cloud-ahhri1kv-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require
   ```

2. **Dependencies are installed**:
   ```bash
   npm install
   ```

3. **Auth tables exist in Neon**:
   ```bash
   npx tsx scripts/test-neon-connection.ts
   ```

## Step 1: Test Database Connection

Run the connection test script:

```bash
cd frontend
npx tsx scripts/test-neon-connection.ts
```

**Expected Output:**
```
✅ DATABASE_URL found
✅ SSL mode configured
🔌 Attempting to connect to Neon...
✅ Connection successful! (XXXms)

Database info:
  Database: neondb
  Timestamp: 2026-01-29...

🔍 Checking Better Auth tables...
✅ Found auth tables:
   - account
   - jwks
   - session
   - user
   - verification

✅ All connection tests passed!
```

**If this fails:**
- Check DATABASE_URL is correct
- Verify Neon project is active in Neon console
- Check network/firewall settings
- Try the connection test a second time (cold start might timeout)

## Step 2: Start Development Server

```bash
npm run dev
```

**Look for in terminal:**
- No error messages about DATABASE_URL
- No NeonDbError messages
- Server starts on http://localhost:3000

**If you see warnings:**
- `⚠️  DATABASE_URL should include '?sslmode=require'` → Add `?sslmode=require` to DATABASE_URL

## Step 3: Test Authentication Flow

### 3.1 Sign Up New User

1. Navigate to http://localhost:3000
2. Click "Sign Up" (or go to http://localhost:3000/signup)
3. Enter:
   - Name: Test User
   - Email: test@example.com
   - Password: password123 (min 8 chars)
4. Click "Sign Up"

**Expected:**
- Form submits successfully
- Redirect to /dashboard
- Dashboard displays "Welcome, Test User"
- NO redirect back to /signin

**Check browser DevTools Network tab:**
- POST /api/auth/sign-up/email → 200 OK
- GET /api/auth/get-session → 200 OK (not 500!)

### 3.2 Sign Out and Sign In

1. Click "Sign Out" button in dashboard
2. Should redirect to /signin
3. Enter credentials:
   - Email: test@example.com
   - Password: password123
4. Click "Sign In"

**Expected:**
- Form submits successfully
- Redirect to /dashboard
- Dashboard displays user info
- NO redirect back to /signin

**Check browser DevTools Network tab:**
- POST /api/auth/sign-in/email → 200 OK
- GET /api/auth/get-session → 200 OK (not 500!)

### 3.3 Page Refresh (Session Persistence)

1. While on /dashboard, press F5 or Ctrl+R to refresh
2. Wait for page to load

**Expected:**
- Page reloads successfully
- User remains logged in
- Dashboard displays user info
- NO redirect to /signin

**Check browser DevTools Network tab:**
- GET /api/auth/get-session → 200 OK

### 3.4 Direct Navigation

1. Manually navigate to http://localhost:3000/dashboard in address bar
2. Wait for page to load

**Expected:**
- Dashboard loads successfully
- User info displayed
- NO redirect to /signin (if already logged in)
- OR redirect to /signin (if not logged in)

## Step 4: Monitor for Errors

### Browser Console

Open DevTools → Console tab

**Should NOT see:**
- "Failed query: select from jwks"
- "NeonDbError"
- "ETIMEDOUT"
- "ENETUNREACH"
- "TypeError: fetch failed"

**OK to see:**
- Normal React hydration warnings
- Info logs from Better Auth

### Terminal (Dev Server)

**Should NOT see:**
- NeonDbError stack traces
- Connection timeout errors
- 500 errors for /api/auth routes

**OK to see:**
- GET /api/auth/get-session 200
- POST /api/auth/sign-in/email 200
- Normal Next.js compilation messages

### Network Tab

Check all auth-related requests:

**GET /api/auth/get-session:**
- Status: 200 OK
- Response time: 50-500ms (cold start: up to 15s for first request)
- Response body: JSON with user session data

**POST /api/auth/sign-in/email:**
- Status: 200 OK
- Response time: 100-800ms
- Response body: JSON with user and session data

## Step 5: Test Edge Cases

### 5.1 Multiple Tabs

1. Open dashboard in Tab 1
2. Open dashboard in Tab 2
3. Sign out in Tab 1
4. Try to use Tab 2

**Expected:**
- Tab 2 should detect signed out state
- May need refresh to redirect to /signin

### 5.2 Long Session

1. Sign in
2. Wait 5+ minutes on dashboard
3. Navigate to different page or refresh

**Expected:**
- Session still valid (7-day expiry)
- No redirect to /signin

### 5.3 Invalid Credentials

1. Go to /signin
2. Enter wrong password
3. Submit form

**Expected:**
- Error message displayed
- NO database timeout errors
- Stays on /signin page

## Debugging Failed Tests

### "Connection timeout" during test

**Cause:** Neon database cold start (first query after idle)

**Solution:**
- Wait 10-30 seconds and try again
- Neon wakes up on first query, subsequent queries are fast

### "GET /api/auth/get-session → 500"

**Cause:** Auth route still running on Edge Runtime

**Fix:**
1. Verify `/frontend/src/app/api/auth/[...all]/route.ts` contains:
   ```typescript
   export const runtime = 'nodejs';
   ```
2. Restart dev server (Ctrl+C and `npm run dev`)
3. Clear browser cache and cookies

### "Session expired" redirect loop

**Cause:** Database connectivity still failing OR browser cookies corrupted

**Fix:**
1. Clear all cookies for localhost:3000:
   - DevTools → Application → Cookies → Delete all
2. Verify connection test passes:
   ```bash
   npx tsx scripts/test-neon-connection.ts
   ```
3. Check terminal for database errors
4. Restart dev server

### "DATABASE_URL not found"

**Cause:** Environment variables not loaded

**Fix:**
1. Create `/frontend/.env.local` if missing
2. Copy contents from `.env.local` template
3. Add your actual DATABASE_URL from Neon console
4. Restart dev server

## Performance Benchmarks

### Normal Operation (After Fix)

| Operation | Expected Time | Max Acceptable |
|-----------|---------------|----------------|
| Sign up | 100-500ms | 2s |
| Sign in | 100-500ms | 2s |
| Get session (warm) | 50-200ms | 500ms |
| Get session (cold start) | 5-15s | 30s |
| Page refresh | 100-400ms | 1s |

### Cold Start Behavior

**First request after 5+ minutes idle:**
- Neon database wakes up: 5-15 seconds
- This is NORMAL for serverless databases
- Subsequent requests are fast (<500ms)

**NOT normal:**
- Consistent timeouts (30s+)
- Every request taking 5+ seconds
- 500 errors even after cold start

## Success Criteria

All tests pass when:

- [x] Connection test script succeeds
- [x] Sign up completes without redirect loop
- [x] Sign in works and stays logged in
- [x] Page refresh preserves session
- [x] GET /api/auth/get-session returns 200 (not 500)
- [x] No database timeout errors in logs
- [x] No ETIMEDOUT/ENETUNREACH errors
- [x] Session persists across page navigations

## Next Steps After Success

1. **Test with backend integration:**
   - Start FastAPI backend
   - Test JWT token flow
   - Verify protected routes work

2. **Add tasks feature:**
   - Create task CRUD endpoints
   - Test user-scoped data access
   - Verify authentication required

3. **Deploy to production:**
   - Update BETTER_AUTH_URL to production URL
   - Use secure cookies (NODE_ENV=production)
   - Monitor cold start times

## Support

If tests still fail after following this guide:

1. Check `/frontend/docs/NEON_CONNECTION_FIX.md` for detailed troubleshooting
2. Run connection test with verbose logging
3. Check Neon console for database status
4. Verify all files match expected configuration
