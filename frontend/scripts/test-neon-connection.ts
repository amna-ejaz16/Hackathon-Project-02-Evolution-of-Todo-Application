/**
 * Test script to verify Neon PostgreSQL connectivity.
 * Run with: npx tsx scripts/test-neon-connection.ts
 */

import { neon } from "@neondatabase/serverless";
import * as dotenv from "dotenv";
import * as path from "path";

// Load environment variables
dotenv.config({ path: path.join(__dirname, "../.env.local") });

async function testConnection() {
  console.log("🔍 Testing Neon PostgreSQL connection...\n");

  // Check DATABASE_URL
  if (!process.env.DATABASE_URL) {
    console.error("❌ DATABASE_URL not found in environment variables");
    console.error("   Make sure .env.local exists and contains DATABASE_URL");
    process.exit(1);
  }

  console.log("✅ DATABASE_URL found");
  console.log(`   Connection string: ${process.env.DATABASE_URL.replace(/:[^:@]+@/, ":***@")}\n`);

  // Check SSL mode
  if (!process.env.DATABASE_URL.includes("sslmode=require")) {
    console.warn("⚠️  DATABASE_URL missing '?sslmode=require' parameter");
    console.warn("   Neon requires SSL - connection may fail\n");
  } else {
    console.log("✅ SSL mode configured\n");
  }

  // Test connection
  try {
    const sql = neon(process.env.DATABASE_URL, {
      fetchOptions: {
        signal: undefined,
      },
    });

    console.log("🔌 Attempting to connect to Neon...");
    const start = Date.now();

    // Simple query to test connectivity
    const result = await sql`SELECT current_database(), version(), now()`;
    const duration = Date.now() - start;

    console.log(`✅ Connection successful! (${duration}ms)\n`);
    console.log("Database info:");
    console.log(`  Database: ${result[0].current_database}`);
    console.log(`  Timestamp: ${result[0].now}\n`);

    // Test auth tables exist
    console.log("🔍 Checking Better Auth tables...");
    const tables = await sql`
      SELECT table_name
      FROM information_schema.tables
      WHERE table_schema = 'public'
      AND table_name IN ('user', 'session', 'account', 'verification', 'jwks')
      ORDER BY table_name
    `;

    if (tables.length === 0) {
      console.error("❌ No Better Auth tables found!");
      console.error("   Run: npm run db:create-auth-tables");
    } else {
      console.log("✅ Found auth tables:");
      tables.forEach((t) => console.log(`   - ${t.table_name}`));
    }

    console.log("\n✅ All connection tests passed!");
  } catch (error) {
    console.error("\n❌ Connection failed!");

    if (error instanceof Error) {
      console.error(`   Error: ${error.message}`);

      // Provide helpful diagnostics
      if (error.message.includes("ETIMEDOUT")) {
        console.error("\n💡 Timeout error - possible causes:");
        console.error("   1. Neon database is cold-starting (wait 10-30 seconds)");
        console.error("   2. Network firewall blocking connection");
        console.error("   3. Incorrect connection string");
      } else if (error.message.includes("ENETUNREACH")) {
        console.error("\n💡 Network unreachable - possible causes:");
        console.error("   1. Running on Edge runtime (should use Node.js)");
        console.error("   2. Network connectivity issues");
        console.error("   3. Neon endpoint region not accessible");
      } else if (error.message.includes("authentication failed")) {
        console.error("\n💡 Authentication failed:");
        console.error("   1. Check DATABASE_URL credentials");
        console.error("   2. Verify Neon project is active");
      }
    }

    process.exit(1);
  }
}

testConnection();
