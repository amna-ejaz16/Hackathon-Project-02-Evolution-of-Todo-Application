/**
 * Script to create Better Auth tables in Neon PostgreSQL.
 * Run with: node scripts/setup-auth-db.js
 */

const { Pool } = require('pg');
const fs = require('fs');
const path = require('path');

// Load environment variables from .env.local
function loadEnv() {
  const envPath = path.join(__dirname, '..', '.env.local');
  const envContent = fs.readFileSync(envPath, 'utf8');
  envContent.split('\n').forEach(line => {
    const [key, ...valueParts] = line.split('=');
    if (key && valueParts.length > 0) {
      process.env[key.trim()] = valueParts.join('=').trim();
    }
  });
}

loadEnv();

async function main() {
  const connectionString = process.env.DATABASE_URL;

  if (!connectionString) {
    console.error('ERROR: DATABASE_URL not found in .env.local');
    process.exit(1);
  }

  console.log('Connecting to Neon PostgreSQL...');

  const pool = new Pool({ connectionString });

  try {
    // Read SQL file
    const sqlPath = path.join(__dirname, 'create-auth-tables.sql');
    const sql = fs.readFileSync(sqlPath, 'utf8');

    console.log('Creating Better Auth tables...');
    await pool.query(sql);

    console.log('✓ Tables created successfully!');
    console.log('  - user');
    console.log('  - session');
    console.log('  - account');
    console.log('  - verification');
    console.log('\nYou can now sign up and sign in.');

  } catch (error) {
    console.error('ERROR:', error.message || error);
    console.error('Full error:', error);
    process.exit(1);
  } finally {
    await pool.end();
  }
}

main();
