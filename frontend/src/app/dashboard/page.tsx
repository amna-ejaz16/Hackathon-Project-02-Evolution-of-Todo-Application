import { headers } from "next/headers";
import { redirect } from "next/navigation";
import { auth } from "@/lib/auth";
import DashboardClient from "./DashboardClient";

// Force dynamic rendering - this page reads headers/cookies for auth
export const dynamic = "force-dynamic";

/**
 * Dashboard Page - Server Component
 *
 * This is a SERVER component that validates the session using Better Auth's
 * server-side session API. This is the CORRECT way to protect routes with
 * Better Auth, NOT client-side useSession() checks.
 *
 * How it works:
 * 1. Gets the session using auth.api.getSession({ headers })
 * 2. If no valid session, redirects to /signin (server-side redirect)
 * 3. If valid session, renders the DashboardClient with user data
 *
 * Benefits:
 * - No flash of unauthenticated content
 * - No client-side redirect loops
 * - Session validated before any client code runs
 * - Works correctly on page refresh
 * - No dependency on /api/auth/session JSON response
 */
export default async function DashboardPage() {
  // Get request headers for session validation
  const headersList = await headers();

  // Validate session server-side using Better Auth's API
  // This reads the session cookie and validates it against the database
  const session = await auth.api.getSession({
    headers: headersList,
  });

  // Debug logging (server-side)
  console.log("[Dashboard] Server-side session check:", {
    hasSession: !!session,
    userId: session?.user?.id,
    userEmail: session?.user?.email,
  });

  // If no valid session, redirect to signin
  // This is a server-side redirect, so no flash of content
  if (!session || !session.user) {
    console.log("[Dashboard] No valid session, redirecting to /signin");
    redirect("/signin");
  }

  // Session is valid - render the dashboard with user data
  // The client component receives the validated user info
  return (
    <DashboardClient
      user={{
        id: session.user.id,
        email: session.user.email,
        name: session.user.name,
      }}
    />
  );
}
