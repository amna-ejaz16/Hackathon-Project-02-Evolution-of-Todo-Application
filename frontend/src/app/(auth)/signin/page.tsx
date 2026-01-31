/**
 * Signin Page - Server Component
 *
 * This server component checks if the user is already authenticated.
 * If authenticated, redirects to dashboard.
 * If not, renders the signin form.
 *
 * T029-T033: User login with email and password.
 */

import { headers } from "next/headers";
import { redirect } from "next/navigation";
import { auth } from "@/lib/auth";
import SigninForm from "./SigninForm";

// Force dynamic rendering - this page reads headers/cookies for auth
export const dynamic = "force-dynamic";

export default async function SigninPage() {
  // Check if user is already authenticated
  const headersList = await headers();
  const session = await auth.api.getSession({
    headers: headersList,
  });

  // If already authenticated, redirect to dashboard
  if (session?.user) {
    console.log("[Signin] User already authenticated, redirecting to dashboard");
    redirect("/dashboard");
  }

  // Not authenticated - render the signin form
  return <SigninForm />;
}
