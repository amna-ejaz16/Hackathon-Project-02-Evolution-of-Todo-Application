"use client";

import { useEffect, useState } from "react";
import { useSession, signOut } from "@/lib/auth-client";

export default function DebugPage() {
  const { data: session, isPending, error, refetch } = useSession();
  const [cookies, setCookies] = useState<string>("");
  const [sessionResponse, setSessionResponse] = useState<string>("");
  const [sessionHeaders, setSessionHeaders] = useState<string>("");
  const [dbTestResponse, setDbTestResponse] = useState<string>("Loading...");
  const [authTestResponse, setAuthTestResponse] = useState<string>("Loading...");
  const [cookieTestResult, setCookieTestResult] = useState<string>("");

  // Test if cookies can be set at all
  const testCookieSetting = () => {
    // Try to set a test cookie
    document.cookie = "debug-test=works; path=/; SameSite=Lax";
    const testCookie = document.cookie.includes("debug-test=works");
    setCookieTestResult(testCookie ? "Cookie test PASSED - cookies work!" : "Cookie test FAILED - cookies blocked!");

    // Update cookies display
    setCookies(document.cookie || "No cookies found");
  };

  // Force session refresh
  const handleRefreshSession = async () => {
    if (refetch) {
      await refetch();
      setCookies(document.cookie || "No cookies found");
    }
  };

  // Clear all cookies (for testing)
  const handleClearCookies = () => {
    document.cookie.split(";").forEach((c) => {
      document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
    });
    setCookies(document.cookie || "No cookies found");
    window.location.reload();
  };

  useEffect(() => {
    // Get cookies
    setCookies(document.cookie || "No cookies found");

    // Run cookie test
    testCookieSetting();

    // Test database connection first
    fetch("/api/test-db")
      .then((res) => res.json())
      .then((data) => setDbTestResponse(JSON.stringify(data, null, 2)))
      .catch((err) => setDbTestResponse(`Error: ${err.message}`));

    // Test Better Auth directly
    fetch("/api/test-auth")
      .then((res) => res.json())
      .then((data) => setAuthTestResponse(JSON.stringify(data, null, 2)))
      .catch((err) => setAuthTestResponse(`Error: ${err.message}`));

    // Manually fetch session endpoint with timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

    fetch("/api/auth/session", {
      credentials: "include",
      signal: controller.signal,
    })
      .then((res) => {
        clearTimeout(timeoutId);
        // Capture response headers
        const headers: Record<string, string> = {};
        res.headers.forEach((value, key) => {
          headers[key] = value;
        });
        setSessionHeaders(JSON.stringify(headers, null, 2));
        return res.text(); // Get raw text first
      })
      .then((text) => {
        try {
          const data = JSON.parse(text);
          setSessionResponse(JSON.stringify(data, null, 2));
        } catch {
          setSessionResponse(`Raw response: ${text}`);
        }
      })
      .catch((err) => {
        clearTimeout(timeoutId);
        if (err.name === "AbortError") {
          setSessionResponse("Error: Request timed out after 10 seconds (database connection issue?)");
        } else {
          setSessionResponse(`Error: ${err.message}`);
        }
      });
  }, []);

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Auth Debug Page</h1>

      <div className="space-y-6">
        {/* Cookie Test Result */}
        <div className={`p-4 rounded ${cookieTestResult.includes("PASSED") ? "bg-green-100" : "bg-red-100"}`}>
          <h2 className="font-semibold mb-2">Cookie Capability Test:</h2>
          <p className="text-sm">{cookieTestResult || "Testing..."}</p>
        </div>

        <div className="bg-blue-100 p-4 rounded">
          <h2 className="font-semibold mb-2">Database Connection Test (/api/test-db):</h2>
          <pre className="text-sm overflow-auto">
            {dbTestResponse}
          </pre>
        </div>

        <div className="bg-yellow-100 p-4 rounded">
          <h2 className="font-semibold mb-2">Better Auth Direct Test (/api/test-auth):</h2>
          <pre className="text-sm overflow-auto">
            {authTestResponse}
          </pre>
        </div>

        <div className="bg-gray-100 p-4 rounded">
          <h2 className="font-semibold mb-2">useSession() Hook Result:</h2>
          <pre className="text-sm overflow-auto">
            isPending: {String(isPending)}{"\n"}
            error: {error ? JSON.stringify(error) : "null"}{"\n"}
            session: {session ? JSON.stringify(session, null, 2) : "null"}
          </pre>
        </div>

        <div className="bg-gray-100 p-4 rounded">
          <h2 className="font-semibold mb-2">Cookies (document.cookie):</h2>
          <pre className="text-sm overflow-auto whitespace-pre-wrap break-all">
            {cookies}
          </pre>
          <p className="text-xs text-gray-500 mt-2">
            Note: HttpOnly cookies won't appear here but will still be sent with requests.
          </p>
        </div>

        <div className="bg-gray-100 p-4 rounded">
          <h2 className="font-semibold mb-2">Direct /api/auth/session Response:</h2>
          <pre className="text-sm overflow-auto">
            {sessionResponse || "Loading..."}
          </pre>
        </div>

        <div className="bg-gray-100 p-4 rounded">
          <h2 className="font-semibold mb-2">Session Response Headers:</h2>
          <pre className="text-sm overflow-auto">
            {sessionHeaders || "Loading..."}
          </pre>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap gap-4">
          <button
            onClick={handleRefreshSession}
            className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
          >
            Refresh Session
          </button>
          <button
            onClick={handleClearCookies}
            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Clear Cookies
          </button>
          <button
            onClick={() => signOut()}
            className="px-4 py-2 bg-orange-600 text-white rounded hover:bg-orange-700"
          >
            Sign Out
          </button>
        </div>

        {/* Navigation */}
        <div className="flex flex-wrap gap-4 pt-4 border-t">
          <a
            href="/signin"
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Go to Sign In
          </a>
          <a
            href="/signup"
            className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
          >
            Go to Sign Up
          </a>
          <a
            href="/dashboard"
            className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700"
          >
            Go to Dashboard
          </a>
        </div>
      </div>
    </div>
  );
}
