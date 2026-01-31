/**
 * Signup Page - Server Component
 *
 * This server component checks if the user is already authenticated.
 * If authenticated, redirects to dashboard.
 * If not, renders the signup form.
 *
 * T023-T028: User registration with email, password, name.
 */

import { headers } from "next/headers";
import { redirect } from "next/navigation";
import { auth } from "@/lib/auth";
import SignupForm from "./SignupForm";

// Force dynamic rendering - this page reads headers/cookies for auth
export const dynamic = "force-dynamic";

export default async function SignupPage() {
  // Check if user is already authenticated
  const headersList = await headers();
  const session = await auth.api.getSession({
    headers: headersList,
  });

  // If already authenticated, redirect to dashboard
  if (session?.user) {
    console.log("[Signup] User already authenticated, redirecting to dashboard");
    redirect("/dashboard");
  }

  // Not authenticated - render the signup form
  return <SignupForm />;
}
