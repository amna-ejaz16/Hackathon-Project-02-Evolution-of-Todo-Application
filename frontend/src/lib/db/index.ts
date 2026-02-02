/**
 * Database connection module for Neon PostgreSQL.
 *
 * Uses WebSocket driver for reliable connections in:
 * - WSL2 environments (avoids IPv6/ETIMEDOUT issues)
 * - Serverless/Edge environments
 * - Cold start scenarios
 */

import { Pool, neonConfig } from "@neondatabase/serverless";
import { drizzle } from "drizzle-orm/neon-serverless";
import * as schema from "./schema";
import ws from "ws";

// Configure WebSocket for Node.js environment
neonConfig.webSocketConstructor = ws;

// Singleton pool instance
let poolInstance: Pool | null = null;

/**
 * Get or create the database connection pool.
 * Uses singleton pattern to prevent connection exhaustion.
 */
export function getPool(): Pool {
  if (!poolInstance) {
    if (!process.env.DATABASE_URL) {
      throw new Error("DATABASE_URL is not configured");
    }

    poolInstance = new Pool({
      connectionString: process.env.DATABASE_URL,
      max: 10,
      idleTimeoutMillis: 30000,
      connectionTimeoutMillis: 10000,
    });

    // Handle pool errors
    poolInstance.on("error", (err: Error) => {
      console.error("Database pool error:", err.message);
      // Reset pool on fatal errors
      if (err.message.includes("terminating connection")) {
        poolInstance = null;
      }
    });
  }

  return poolInstance;
}

/**
 * Get Drizzle ORM instance.
 */
export function getDb() {
  return drizzle(getPool(), { schema });
}

/**
 * Execute a database query with automatic retry on connection failures.
 *
 * @param queryFn - Function that executes the query
 * @param maxRetries - Maximum retry attempts (default: 3)
 * @param baseDelayMs - Base delay for exponential backoff (default: 500ms)
 */
export async function withRetry<T>(
  queryFn: () => Promise<T>,
  maxRetries: number = 3,
  baseDelayMs: number = 500
): Promise<T> {
  let lastError: Error | null = null;

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await queryFn();
    } catch (error) {
      lastError = error as Error;
      const errorMessage = lastError.message || "";

      // Check if error is retryable (connection issues)
      const isRetryable =
        errorMessage.includes("ETIMEDOUT") ||
        errorMessage.includes("ENETUNREACH") ||
        errorMessage.includes("ECONNREFUSED") ||
        errorMessage.includes("ECONNRESET") ||
        errorMessage.includes("connection") ||
        errorMessage.includes("timeout");

      if (!isRetryable || attempt === maxRetries) {
        throw lastError;
      }

      // Exponential backoff: 500ms, 1000ms, 2000ms
      const delayMs = baseDelayMs * Math.pow(2, attempt - 1);
      console.warn(
        `Database query failed (attempt ${attempt}/${maxRetries}): ${errorMessage}. ` +
        `Retrying in ${delayMs}ms...`
      );

      await new Promise((resolve) => setTimeout(resolve, delayMs));
    }
  }

  throw lastError;
}

/**
 * Test database connectivity.
 * Returns true if connection successful, false otherwise.
 */
export async function testConnection(): Promise<boolean> {
  try {
    const pool = getPool();
    const client = await pool.connect();
    await client.query("SELECT 1");
    client.release();
    return true;
  } catch (error) {
    console.error("Database connection test failed:", error);
    return false;
  }
}
