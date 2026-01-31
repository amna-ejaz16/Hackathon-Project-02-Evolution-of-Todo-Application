import { auth } from "@/lib/auth";
import { NextResponse } from "next/server";

export async function GET() {
  try {
    // Try to access Better Auth's internal API
    const response = await auth.api.getSession({
      headers: new Headers(),
    });

    return NextResponse.json({
      success: true,
      session: response,
    });
  } catch (error) {
    console.error("Better Auth error:", error);
    return NextResponse.json({
      success: false,
      error: error instanceof Error ? error.message : String(error),
      stack: error instanceof Error ? error.stack : undefined,
    }, { status: 500 });
  }
}
