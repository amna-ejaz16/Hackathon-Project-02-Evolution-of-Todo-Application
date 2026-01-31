import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Route protection middleware.
 *
 * DISABLED - All route protection is handled by Server Components.
 *
 * The authentication architecture uses:
 * 1. Server Components with auth.api.getSession() for route protection
 * 2. Server-side redirects via next/navigation redirect()
 * 3. No client-side auth checks or redirects
 *
 * This approach:
 * - Prevents redirect loops
 * - No flash of unauthenticated content
 * - Works correctly on page refresh
 * - Avoids dependency on /api/auth/session JSON response
 *
 * See:
 * - /app/dashboard/page.tsx - Protected route example
 * - /app/(auth)/signin/page.tsx - Auth redirect for logged-in users
 */

export function middleware(_request: NextRequest) {
  // Middleware disabled - auth handled by Server Components
  return NextResponse.next();
}

export const config = {
  // Match nothing - effectively disables middleware
  matcher: [],
};
