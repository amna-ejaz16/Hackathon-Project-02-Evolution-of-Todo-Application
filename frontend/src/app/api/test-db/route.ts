import { Pool } from "@neondatabase/serverless";
import { NextResponse } from "next/server";

export async function GET() {
  const startTime = Date.now();

  try {
    const pool = new Pool({
      connectionString: process.env.DATABASE_URL,
    });

    // Test query
    const result = await pool.query('SELECT NOW() as time, current_database() as db');

    await pool.end();

    return NextResponse.json({
      success: true,
      time: result.rows[0].time,
      database: result.rows[0].db,
      latency: `${Date.now() - startTime}ms`,
    });
  } catch (error) {
    return NextResponse.json({
      success: false,
      error: error instanceof Error ? error.message : "Unknown error",
      latency: `${Date.now() - startTime}ms`,
    }, { status: 500 });
  }
}
