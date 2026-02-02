import { createAuthClient } from "better-auth/react";

/**
 * Better Auth client for React components.
 *
 * Provides hooks and utilities for:
 * - useSession() - Get current session
 * - signIn.email() - Sign in with email/password
 * - signUp.email() - Register new account
 * - signOut() - Sign out current user
 *
 * NOTE: JWT tokens are obtained via the custom /api/auth/token endpoint,
 * NOT through Better Auth's JWT plugin (which has JWKS initialization issues).
 * Use the getToken() function exported from this module for API authentication.
 *
 * COOKIE FIX: fetchOptions.credentials must be 'include' to send/receive cookies
 * on same-origin requests. Without this, session cookies won't be sent with
 * requests to /api/auth/* endpoints.
 */
export const authClient = createAuthClient({
  baseURL: process.env.NEXT_PUBLIC_BETTER_AUTH_URL || "http://localhost:3000",
  // CRITICAL: Enable credentials for all fetch requests
  // This ensures cookies are sent with every request to Better Auth endpoints
  fetchOptions: {
    credentials: "include" as RequestCredentials,
  },
});

// Export commonly used hooks and methods
export const {
  useSession,
  signIn,
  signUp,
  signOut,
  getSession,
} = authClient;

/**
 * Sleep utility for retry delays.
 */
function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Get JWT token for API authentication with retry logic.
 *
 * This function retrieves a JWT token from Better Auth's /api/auth/token endpoint.
 * The token is used to authenticate requests to the backend API.
 *
 * CRITICAL FIX: Implements exponential backoff retry to handle the race condition
 * where Better Auth's session cookie exists but the server hasn't fully processed
 * the session yet. This is especially important immediately after signin.
 *
 * @param maxRetries Maximum number of retry attempts (default: 3)
 * @returns JWT token string if available, null if not authenticated after retries
 */
export async function getToken(maxRetries: number = 3): Promise<string | null> {
  const baseUrl = process.env.NEXT_PUBLIC_BETTER_AUTH_URL || "http://localhost:3000";
  const tokenUrl = `${baseUrl}/api/auth/token`;

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      // Use native fetch with explicit credentials to ensure session cookie is sent
      const response = await fetch(tokenUrl, {
        method: "GET",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
      });

      // Debug logging in development
      if (process.env.NODE_ENV === "development") {
        console.log(`getToken attempt ${attempt}/${maxRetries}, status:`, response.status);
      }

      // If 401, this means no valid session - don't retry
      if (response.status === 401) {
        console.warn("getToken: No valid session (401)");
        return null;
      }

      // For other errors, retry with exponential backoff
      if (!response.ok) {
        const errorText = await response.text();
        console.warn(
          `getToken attempt ${attempt}/${maxRetries} failed: ${response.status} - ${errorText}`
        );

        // If this isn't the last attempt, retry after delay
        if (attempt < maxRetries) {
          const delayMs = Math.pow(2, attempt - 1) * 200; // 200ms, 400ms, 800ms
          console.log(`Retrying after ${delayMs}ms...`);
          await sleep(delayMs);
          continue;
        }

        // Last attempt failed
        return null;
      }

      const data = await response.json();

      // Debug: log response structure in development
      if (process.env.NODE_ENV === "development") {
        console.log("getToken response data:", data);
      }

      // Handle various response structures Better Auth might return
      if (!data) {
        console.warn("getToken: Empty response from /token endpoint");
        if (attempt < maxRetries) {
          const delayMs = Math.pow(2, attempt - 1) * 200;
          await sleep(delayMs);
          continue;
        }
        return null;
      }

      // Better Auth JWT plugin returns { token: "..." }
      // But we check multiple structures for compatibility
      const token =
        (data as { token?: string })?.token ||
        (data as { data?: { token?: string } })?.data?.token ||
        null;

      if (!token) {
        console.warn("getToken: No token found in response", data);
        if (attempt < maxRetries) {
          const delayMs = Math.pow(2, attempt - 1) * 200;
          await sleep(delayMs);
          continue;
        }
        return null;
      }

      // Success - return the token
      if (process.env.NODE_ENV === "development") {
        console.log("getToken: Successfully obtained token");
      }
      return token;
    } catch (error) {
      // Network errors or other exceptions
      console.error(`getToken attempt ${attempt}/${maxRetries} exception:`, error);

      // Retry on network errors
      if (attempt < maxRetries) {
        const delayMs = Math.pow(2, attempt - 1) * 200;
        console.log(`Retrying after ${delayMs}ms due to error...`);
        await sleep(delayMs);
        continue;
      }

      // Last attempt failed
      return null;
    }
  }

  // Should never reach here, but TypeScript needs this
  return null;
}
