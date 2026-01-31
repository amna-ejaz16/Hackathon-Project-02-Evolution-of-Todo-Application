#!/usr/bin/env npx tsx
/**
 * Database Connection Test Script
 *
 * Tests Neon PostgreSQL connectivity using WebSocket driver.
 * Run: npx tsx scripts/test-db.ts
 */

import { Pool, neonConfig } from "@neondatabase/serverless";
import * as dotenv from "dotenv";
import ws from "ws";

// Load environment variables
dotenv.config({ path: ".env.local" });

// Configure WebSocket
neonConfig.webSocketConstructor = ws;

async function testConnection() {
  console.log("🔍 Testing Neon PostgreSQL Connection...\n");

  // Check DATABASE_URL
  const dbUrl = process.env.DATABASE_URL;
  if (!dbUrl) {
    console.error("❌ DATABASE_URL not found in .env.local");
    process.exit(1);
  }

  // Mask password in URL for display
  const maskedUrl = dbUrl.replace(/:[^:@]+@/, ":****@");
  console.log(`📡 Connection string: ${maskedUrl}`);
  console.log(`✅ SSL mode: ${dbUrl.includes("sslmode=require") ? "enabled" : "⚠️ MISSING"}`);
  console.log(`✅ Pooler: ${dbUrl.includes("-pooler") ? "enabled" : "direct connection"}\n`);

  // Create pool
  const pool = new Pool({
    connectionString: dbUrl,
    max: 1,
    connectionTimeoutMillis: 15000, // 15s timeout for cold starts
  });

  try {
    console.log("⏳ Connecting (this may take 5-15s on cold start)...");
    const startTime = Date.now();

    // Test basic connectivity
    const client = await pool.connect();
    const connectTime = Date.now() - startTime;
    console.log(`✅ Connected in ${connectTime}ms\n`);

    // Test query
    const result = await client.query("SELECT NOW() as time, current_database() as db");
    console.log(`✅ Query successful`);
    console.log(`   Database: ${result.rows[0].db}`);
    console.log(`   Server time: ${result.rows[0].time}\n`);

    // Check auth tables exist
    console.log("📋 Checking Better Auth tables...");
    const tables = await client.query(`
      SELECT table_name
      FROM information_schema.tables
      WHERE table_schema = 'public'
        AND table_name IN ('user', 'session', 'account', 'verification', 'jwks')
      ORDER BY table_name
    `);

    const foundTables = tables.rows.map((r: { table_name: string }) => r.table_name);
    const requiredTables = ["user", "session", "account", "verification", "jwks"];

    for (const table of requiredTables) {
      if (foundTables.includes(table)) {
        console.log(`   ✅ ${table}`);
      } else {
        console.log(`   ❌ ${table} (MISSING)`);
      }
    }

    client.release();
    await pool.end();

    console.log("\n🎉 All connection tests passed!");
    console.log("   Your Neon PostgreSQL connection is working correctly.\n");

  } catch (error) {
    const err = error as Error;
    console.error(`\n❌ Connection failed: ${err.message}`);

    // Provide helpful diagnostics
    if (err.message.includes("ETIMEDOUT")) {
      console.log("\n💡 ETIMEDOUT usually means:");
      console.log("   - Neon database is in cold start (wait and retry)");
      console.log("   - Network/firewall blocking connection");
      console.log("   - WSL2 IPv6 issues (try restarting WSL)");
    } else if (err.message.includes("ENETUNREACH")) {
      console.log("\n💡 ENETUNREACH usually means:");
      console.log("   - Network is unreachable");
      console.log("   - WSL2 network issue - try: wsl --shutdown");
      console.log("   - Then restart your terminal");
    } else if (err.message.includes("password")) {
      console.log("\n💡 Authentication error:");
      console.log("   - Check your DATABASE_URL password is correct");
      console.log("   - Regenerate credentials in Neon dashboard if needed");
    }

    await pool.end();
    process.exit(1);
  }
}

testConnection();
