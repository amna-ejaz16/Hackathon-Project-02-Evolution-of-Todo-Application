/**
 * Signin form client component.
 * T029-T033: User login with email and password.
 */

"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { signIn } from "@/lib/auth-client";

export default function SigninForm() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  // T030: Connect signin form to Better Auth signIn.email()
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Basic client-side validation
    if (!email || !password) {
      setError("Please fill in all fields");
      return;
    }

    setIsLoading(true);

    try {
      const result = await signIn.email({
        email,
        password,
      });

      if (result.error) {
        // T031: Generic error message - never reveal if email exists
        setError("Invalid credentials. Please check your email and password.");
        setIsLoading(false);
        return;
      }

      // T032: Redirect to dashboard after successful signin
      // Add a small delay to ensure Better Auth's session cookies are set
      console.log("Signin successful, waiting for session to stabilize...");
      await new Promise((resolve) => setTimeout(resolve, 200));

      console.log("Redirecting to dashboard...");
      // Use window.location for a full page navigation to trigger server-side auth check
      window.location.href = "/dashboard";
    } catch (err) {
      // T031: Handle unexpected errors with generic message
      setError("Invalid credentials. Please check your email and password.");
      console.error("Signin error:", err);
      setIsLoading(false);
    }
    // Note: Don't set isLoading(false) here because we're redirecting
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-dark-950 px-4 py-12 relative overflow-hidden">
      {/* Background gradient effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-neon-purple/20 rounded-full blur-[100px]" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-neon-magenta/20 rounded-full blur-[100px]" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md relative z-10"
      >
        {/* Card container */}
        <div className="card-glow p-8 space-y-6">
          {/* App Branding */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1, duration: 0.4 }}
            className="text-center"
          >
            {/* Logo + App Name */}
            <div className="flex items-center justify-center gap-3 mb-4">
              {/* Tick/Checkmark Logo */}
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-neon-purple to-neon-magenta flex items-center justify-center shadow-neon-md">
                <svg
                  className="w-7 h-7 text-white"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={3}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>
              <h1 className="text-2xl font-bold text-gradient">Task Manager</h1>
            </div>

            {/* Header */}
            <h2 className="text-2xl font-bold text-white">Sign In</h2>
            <p className="mt-2 text-sm text-gray-400">
              Sign in to continue to your tasks
            </p>
          </motion.div>

          {/* T029: Signin form with email and password fields */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* General error message */}
            {error && (
              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl"
                role="alert"
                aria-live="polite"
              >
                <p className="text-sm text-red-400">{error}</p>
              </motion.div>
            )}

            {/* Email field */}
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
            >
              <label
                htmlFor="email"
                className="block text-sm font-medium text-gray-300 mb-2"
              >
                Email <span className="text-neon-magenta">*</span>
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  setError(null); // Clear error on input change
                }}
                placeholder="you@example.com"
                required
                aria-required="true"
                aria-invalid={!!error}
                autoComplete="email"
                className="input-dark"
              />
            </motion.div>

            {/* Password field */}
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.25 }}
            >
              <label
                htmlFor="password"
                className="block text-sm font-medium text-gray-300 mb-2"
              >
                Password <span className="text-neon-magenta">*</span>
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  setError(null); // Clear error on input change
                }}
                placeholder="Your password"
                required
                aria-required="true"
                aria-invalid={!!error}
                autoComplete="current-password"
                className="input-dark"
              />
            </motion.div>

            {/* Submit button */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
            >
              <button
                type="submit"
                disabled={isLoading}
                className="w-full btn-neon py-3 text-base"
              >
                {isLoading ? (
                  <span className="flex items-center justify-center">
                    <svg
                      className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      aria-hidden="true"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      ></circle>
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      ></path>
                    </svg>
                    Signing in...
                  </span>
                ) : (
                  "Sign In"
                )}
              </button>
            </motion.div>
          </form>

          {/* T033: Link to signup page */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="text-center pt-4 border-t border-dark-600"
          >
            <p className="text-sm text-gray-400">
              Don&apos;t have an account?{" "}
              <Link
                href="/signup"
                className="font-medium text-neon-purple hover:text-neon-pink transition-colors"
              >
                Create account
              </Link>
            </p>
          </motion.div>
        </div>

        {/* Additional help text */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-6 text-center text-xs text-gray-500"
        >
          Your privacy and security are our top priorities.
        </motion.p>
      </motion.div>
    </div>
  );
}
