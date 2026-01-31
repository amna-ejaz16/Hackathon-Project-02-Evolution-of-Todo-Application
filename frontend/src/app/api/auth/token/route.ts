/**
 * Custom JWT token endpoint for API authentication.
 *
 * This endpoint generates HS256 JWT tokens for authenticated users.
 * It replaces Better Auth's JWT plugin which has JWKS initialization issues
 * when using custom symmetric signing.
 *
 * Flow:
 * 1. Client requests token with session cookie
 * 2. Server validates session using Better Auth
 * 3. If valid, generates HS256 JWT with user info
 * 4. Returns { token: "..." } for API authentication
 *
 * The backend (FastAPI) verifies these tokens using the same
 * BETTER_AUTH_SECRET with jwt.decode(algorithms=["HS256"]).
 */

import { NextRequest, NextResponse } from "next/server";
import { SignJWT } from "jose";
import { auth } from "@/lib/auth";
import { headers } from "next/headers";

// Force Node.js runtime for database connections
export const runtime = "nodejs";

/**
 * GET /api/auth/token
 *
 * Returns a JWT token for the authenticated user.
 * Requires a valid session cookie.
 */
export async function GET(request: NextRequest) {
  try {
    // Get the session from Better Auth
    // This validates the session cookie automatically
    const session = await auth.api.getSession({
      headers: await headers(),
    });

    // If no session, return 401 Unauthorized
    if (!session || !session.user) {
      return NextResponse.json(
        { error: "Not authenticated" },
        { status: 401 }
      );
    }

    const user = session.user;

    // Validate required secret
    const secret = process.env.BETTER_AUTH_SECRET;
    if (!secret) {
      console.error("[Token API] BETTER_AUTH_SECRET is not configured");
      return NextResponse.json(
        { error: "Server configuration error" },
        { status: 500 }
      );
    }

    // Debug: Log secret info (first 10 chars only for security)
    console.log(`[Token API] Using secret (first 10 chars): ${secret.substring(0, 10)}...`);
    console.log(`[Token API] Secret length: ${secret.length}`);

    // Create JWT payload matching what the backend expects
    // See: backend/src/core/security.py - extract_user_id() and extract_email()
    const payload = {
      id: user.id,
      email: user.email,
    };

    console.log(`[Token API] Creating token for user: ${user.email}, id: ${user.id}`);

    // Encode secret for jose library
    const secretKey = new TextEncoder().encode(secret);

    // Create HS256 JWT token
    // This matches the FastAPI backend's verification:
    // jwt.decode(token, secret, algorithms=["HS256"])
    const token = await new SignJWT(payload)
      .setProtectedHeader({ alg: "HS256", typ: "JWT" })
      .setIssuedAt()
      .setExpirationTime("24h") // Match session duration
      .sign(secretKey);

    // Debug: Log generated token info
    console.log(`[Token API] Generated token (first 50 chars): ${token.substring(0, 50)}...`);

    // Return token in the format expected by auth-client.ts getToken()
    return NextResponse.json({ token });
  } catch (error) {
    console.error("Token generation error:", error);

    // Don't expose internal errors
    return NextResponse.json(
      { error: "Failed to generate token" },
      { status: 500 }
    );
  }
}
