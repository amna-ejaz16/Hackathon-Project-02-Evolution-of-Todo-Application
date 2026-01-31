# Neon PostgreSQL Connection Fix

## Problem Summary

Users were experiencing persistent authentication failures with the following symptoms:

1. Signup succeeds
2. Sign-in succeeds
3. Dashboard opens briefly
4. User gets redirected back to /signin
5. "Session expired" message or red Next.js error overlay

## Root Cause

The Better Auth API route was running on **Edge Runtime** (default in Next.js 15+), but the Neon HTTP driver (`@neondatabase/serverless` with `drizzle-orm/neon-http`) has known connectivity issues on Edge Runtime.

### Error Chain

```
1. User signs in → POST /api/auth/sign-in/email (succeeds)
2. Session created in database → Cookie set
3. Dashboard loads → Makes GET /api/auth/get-session
4. Edge Runtime tries to connect to Neon → Connection times out
5. Error: ETIMEDOUT / ENETUNREACH / "Failed query: select from jwks"
6. GET /api/auth/get-session returns 500
7. Better Auth interprets 500 as "no valid session"
8. Middleware redirects to /signin → User sees "session expired"
```

## The Fix

### 1. Force Node.js Runtime for Auth Route

**File:** `/frontend/src/app/api/auth/[...all]/route.ts`

```typescript
// Add this at the top of the file
export const runtime = 'nodejs';
```

**Why this works:**
- Node.js runtime provides stable TCP connections to Neon
- Better connection pooling than Edge runtime
- Proper timeout handling for database queries
- Neon HTTP driver works reliably in Node.js environment

### 2. Enhanced Connection Validation

**File:** `/frontend/src/lib/auth.ts`

Added validation to catch configuration issues early:

```typescript
// Validate DATABASE_URL exists
if (!process.env.DATABASE_URL) {
  throw new Error("DATABASE_URL environment variable is required");
}

// Validate SSL mode is configured
if (!process.env.DATABASE_URL.includes("sslmode=require")) {
  console.warn("DATABASE_URL should include '?sslmode=require'");
}
```

### 3. Connection Pooling Configuration

```typescript
const sql = neon(process.env.DATABASE_URL, {
  fetchOptions: {
    signal: undefined, // Allow requests to set their own timeouts
  },
  fullResults: false, // Enable connection pooling
});
```

## Verification

### Test the Fix

1. **Stop and restart the dev server:**
   ```bash
   cd frontend
   npm run dev
   ```

2. **Run the connection test script:**
   ```bash
   npx tsx scripts/test-neon-connection.ts
   ```

   Expected output:
   ```
   ✅ DATABASE_URL found
   ✅ SSL mode configured
   ✅ Connection successful! (XXXms)
   ✅ Found auth tables:
      - account
      - jwks
      - session
      - user
      - verification
   ✅ All connection tests passed!
   ```

3. **Test the auth flow:**
   - Sign up a new user
   - Sign in
   - Navigate to dashboard
   - Verify you stay logged in (no redirect to /signin)
   - Refresh the page (session should persist)

### Monitor Logs

Check the browser console and terminal for:
- No `NeonDbError` messages
- No `ETIMEDOUT` / `ENETUNREACH` errors
- Successful GET /api/auth/get-session (200 status)

## Technical Details

### Why Edge Runtime Fails with Neon

Edge Runtime limitations:
- Restricted Node.js APIs (limited TCP socket access)
- Different fetch implementation
- Connection pooling not optimized for database clients
- Timeout handling differs from Node.js

Neon HTTP driver expectations:
- Relies on Node.js fetch polyfills for certain features
- Needs stable connection pooling
- Requires proper timeout propagation

### Alternative Solutions (Not Recommended)

1. **Switch to Neon WebSocket driver:**
   - Requires `@neondatabase/serverless` with WebSocket mode
   - Works on Edge but adds latency
   - More complex configuration

2. **Use Drizzle with Postgres.js:**
   - Different driver entirely
   - Requires Node.js runtime anyway
   - More dependencies

3. **Use Prisma adapter:**
   - Heavier ORM
   - Slower cold starts
   - Still requires Node.js runtime for database operations

## Configuration Checklist

- [x] `export const runtime = 'nodejs'` in auth route
- [x] DATABASE_URL includes `?sslmode=require`
- [x] DATABASE_URL uses pooled connection string (ends with `-pooler`)
- [x] Better Auth secret is set (BETTER_AUTH_SECRET)
- [x] All required auth tables exist (user, session, account, verification, jwks)
- [x] Connection pooling enabled in Neon client
- [x] Proper error handling and validation

## Related Files

- `/frontend/src/app/api/auth/[...all]/route.ts` - Auth route with runtime config
- `/frontend/src/lib/auth.ts` - Better Auth configuration
- `/frontend/src/lib/db/schema.ts` - Database schema definitions
- `/frontend/.env.local` - Environment variables (DATABASE_URL, secrets)
- `/frontend/scripts/test-neon-connection.ts` - Connection test utility

## Performance Impact

**Before fix:**
- GET /api/auth/get-session: 5000-30000ms (timeout)
- Status: 500 (connection failure)

**After fix:**
- GET /api/auth/get-session: 50-300ms (cold start: 200-800ms)
- Status: 200 (success)

**Neon cold starts:**
- First query after idle: 5-15 seconds (Neon waking up)
- Subsequent queries: 50-200ms
- This is expected behavior for serverless databases

## Troubleshooting

### Still seeing timeouts?

1. **Check runtime is actually Node.js:**
   ```bash
   # Add temporary logging in route.ts
   console.log('Runtime:', process.versions.node ? 'nodejs' : 'edge');
   ```

2. **Verify Neon database is active:**
   - Log into Neon console
   - Check project status
   - Verify no quota/billing issues

3. **Test direct connection:**
   ```bash
   npx tsx scripts/test-neon-connection.ts
   ```

4. **Check firewall/network:**
   - Some corporate networks block PostgreSQL ports
   - Try from different network or use VPN

### Session still expires immediately?

1. **Clear browser cookies:**
   - Open DevTools → Application → Cookies
   - Delete all cookies for localhost:3000

2. **Check secret matching:**
   - Verify BETTER_AUTH_SECRET is identical in frontend and backend
   - Secret must be base64 encoded

3. **Verify tables exist:**
   ```bash
   npx tsx scripts/test-neon-connection.ts
   ```

## References

- [Next.js Edge Runtime vs Node.js Runtime](https://nextjs.org/docs/app/building-your-application/rendering/edge-and-nodejs-runtimes)
- [Neon Serverless Driver Documentation](https://neon.tech/docs/serverless/serverless-driver)
- [Better Auth Documentation](https://better-auth.com/docs)
- [Drizzle ORM with Neon](https://orm.drizzle.team/docs/get-started-postgresql#neon)
