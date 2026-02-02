import { getToken } from "./auth-client";

/**
 * API base URL from environment.
 */
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Custom error class for API errors.
 */
export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    message: string,
    public shouldRedirect: boolean = false
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/**
 * Authenticated fetch utility with improved error handling.
 *
 * Automatically attaches the JWT Bearer token to requests.
 * Handles common error cases with distinction between temporary and permanent failures.
 *
 * CRITICAL FIX: The getToken() function now includes retry logic with exponential
 * backoff to handle Better Auth's session stabilization window after signin.
 * We distinguish between:
 * - No token after retries = genuine auth failure (redirect to signin)
 * - Backend 401 = token expired or invalid (redirect to signin)
 * - Network errors = temporary failures (show error, allow retry)
 *
 * @param endpoint - API endpoint (e.g., "/tasks")
 * @param options - Fetch options
 * @returns Response data
 * @throws ApiError on non-2xx responses
 */
export async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  // Attempt to get token with built-in retry logic (3 attempts)
  const token = await getToken();

  // If no token after all retries, the session is genuinely invalid
  if (!token) {
    console.error("apiFetch: Failed to obtain JWT token after retries - no valid session");
    throw new ApiError(
      401,
      "No Token",
      "Unable to authenticate. Please sign in again.",
      true // Redirect to signin - we confirmed there's no valid session after retries
    );
  }

  // Debug: Log token details
  console.log(`[apiFetch] Token received (first 50 chars): ${token.substring(0, 50)}...`);
  console.log(`[apiFetch] Token length: ${token.length}`);

  // Decode token header for debugging (base64url)
  try {
    const headerB64 = token.split('.')[0];
    const headerJson = atob(headerB64.replace(/-/g, '+').replace(/_/g, '/'));
    console.log(`[apiFetch] Token header: ${headerJson}`);
  } catch (e) {
    console.error(`[apiFetch] Failed to decode token header:`, e);
  }

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...options.headers,
    "Authorization": `Bearer ${token}`,
  };

  console.log(`[apiFetch] Authorization header: Bearer ${token.substring(0, 30)}...`);

  const url = `${API_BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    // Handle 401 Unauthorized - this means token was sent but rejected by backend
    if (response.status === 401) {
      console.error("apiFetch: 401 received - token was rejected by backend");
      throw new ApiError(
        401,
        "Unauthorized",
        "Your session has expired. Please sign in again.",
        true
      );
    }

    // Handle other errors
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const message = errorData.detail || response.statusText;
      // Don't redirect for non-auth errors
      throw new ApiError(response.status, response.statusText, message, false);
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return {} as T;
    }

    return response.json();
  } catch (error) {
    // Re-throw ApiError as-is
    if (error instanceof ApiError) {
      throw error;
    }

    // Network errors or other exceptions - don't redirect, show error
    console.error("apiFetch: Network or unexpected error:", error);
    throw new ApiError(
      0,
      "Network Error",
      "Unable to connect to server. Please check your connection.",
      false
    );
  }
}

/**
 * API helper methods for common operations.
 */
export const api = {
  get: <T>(endpoint: string) => apiFetch<T>(endpoint, { method: "GET" }),

  post: <T>(endpoint: string, data?: unknown) =>
    apiFetch<T>(endpoint, {
      method: "POST",
      body: data ? JSON.stringify(data) : undefined,
    }),

  patch: <T>(endpoint: string, data: unknown) =>
    apiFetch<T>(endpoint, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  delete: <T>(endpoint: string) => apiFetch<T>(endpoint, { method: "DELETE" }),
};
