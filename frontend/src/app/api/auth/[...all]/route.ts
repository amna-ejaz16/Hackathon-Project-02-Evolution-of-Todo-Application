import { auth } from "@/lib/auth";
import { toNextJsHandler } from "better-auth/next-js";
import { NextResponse, NextRequest } from "next/server";

/**
 * CRITICAL: Force Node.js runtime for Better Auth + Neon PostgreSQL.
 *
 * The Neon HTTP driver (@neondatabase/serverless with neon-http) has
 * connectivity issues on Edge Runtime, causing ETIMEDOUT/ENETUNREACH errors.
 * This manifests as session validation failures after successful login.
 *
 * Node.js runtime provides:
 * - Stable TCP connections to Neon
 * - Better connection pooling
 * - Proper timeout handling
 */
export const runtime = "nodejs";

// Use the standard toNextJsHandler
const { GET: _GET, POST: _POST } = toNextJsHandler(auth.handler);

/**
 * Fix cookie attributes for localhost development.
 *
 * The issue: Better Auth may set cookies with Secure=true even on localhost HTTP.
 * Secure cookies are ONLY sent over HTTPS, so they won't work on http://localhost.
 *
 * This function:
 * 1. Parses the Set-Cookie header
 * 2. Removes 'Secure' attribute on non-HTTPS
 * 3. Ensures 'SameSite=Lax' for proper navigation
 */
function fixCookiesForLocalhost(response: Response, request: NextRequest): Response {
  const isSecure = request.url.startsWith("https://");
  const setCookieHeader = response.headers.get("set-cookie");

  if (!setCookieHeader) {
    return response;
  }

  // Split multiple cookies (they're separated by comma but date strings also contain commas)
  // Better Auth typically uses separate Set-Cookie headers via headers.append()
  // but they get joined when accessed via get()
  const cookies = setCookieHeader.split(/,(?=\s*[^;,]+=[^;,]+)/);

  const fixedCookies = cookies.map((cookie) => {
    let fixed = cookie.trim();

    if (!isSecure) {
      // Remove Secure attribute for HTTP (localhost)
      fixed = fixed.replace(/;\s*Secure/gi, "");
    }

    // Ensure SameSite=Lax is present (for navigation)
    if (!/SameSite/i.test(fixed)) {
      fixed += "; SameSite=Lax";
    }

    // Ensure Path=/ is present
    if (!/Path\s*=/i.test(fixed)) {
      fixed += "; Path=/";
    }

    return fixed;
  });

  // Log the fix for debugging
  console.log("[Auth] Original Set-Cookie:", setCookieHeader);
  console.log("[Auth] Fixed Set-Cookie:", fixedCookies.join(", "));

  // Create a new response with fixed cookies
  const newResponse = new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: new Headers(response.headers),
  });

  // Remove old Set-Cookie and add fixed ones
  newResponse.headers.delete("set-cookie");
  fixedCookies.forEach((cookie) => {
    newResponse.headers.append("set-cookie", cookie);
  });

  return newResponse;
}

/**
 * Better Auth API route handler with cookie fix.
 *
 * This catch-all route handles all Better Auth endpoints:
 * - POST /api/auth/sign-in/email
 * - POST /api/auth/sign-up/email
 * - POST /api/auth/sign-out
 * - GET /api/auth/session
 *
 * COOKIE FIX: Ensures cookies work correctly on localhost HTTP
 */
export async function GET(request: NextRequest) {
  const response = await _GET(request);
  return fixCookiesForLocalhost(response, request);
}

export async function POST(request: NextRequest) {
  const response = await _POST(request);
  return fixCookiesForLocalhost(response, request);
}

/**
 * Handle CORS preflight requests.
 */
export async function OPTIONS() {
  return new NextResponse(null, {
    status: 204,
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization",
    },
  });
}
