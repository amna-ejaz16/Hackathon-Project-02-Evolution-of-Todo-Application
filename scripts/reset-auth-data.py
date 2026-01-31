#!/usr/bin/env python3
"""
Database Reset Script for Neon PostgreSQL
==========================================
Purpose: Clear all authentication and user-related data while preserving schema

This script resets:
  1. Better Auth tables (camelCase): user, session, account, verification, jwks
  2. Backend tables (snake_case): users, sessions, accounts, verifications, tasks

Usage:
    python reset-auth-data.py
"""

import psycopg2
import sys
import os
from pathlib import Path

# Load DATABASE_URL from backend/.env
backend_dir = Path(__file__).parent.parent / "backend"
env_file = backend_dir / ".env"

DATABASE_URL = None

if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if line.strip().startswith("DATABASE_URL="):
                DATABASE_URL = line.strip().split("=", 1)[1]
                break

if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found in backend/.env")
    sys.exit(1)

print("=" * 80)
print("NEON POSTGRESQL DATABASE RESET")
print("=" * 80)
print(f"\nConnecting to: {DATABASE_URL.split('@')[1].split('/')[0]}...")

try:
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    cur = conn.cursor()

    print("\n" + "=" * 80)
    print("STEP 1: Checking current state")
    print("=" * 80)

    # Display current state
    cur.execute("""
        SELECT
            'account' AS table_name,
            COUNT(*) AS row_count
        FROM account
        UNION ALL
        SELECT 'session', COUNT(*) FROM session
        UNION ALL
        SELECT 'verification', COUNT(*) FROM verification
        UNION ALL
        SELECT 'jwks', COUNT(*) FROM jwks
        UNION ALL
        SELECT 'user', COUNT(*) FROM "user"
        UNION ALL
        SELECT 'tasks', COUNT(*) FROM tasks
        UNION ALL
        SELECT 'users', COUNT(*) FROM users;
    """)

    before_counts = cur.fetchall()
    print("\nBEFORE RESET - Row Counts:")
    for table, count in before_counts:
        print(f"  {table}: {count} rows")

    print("\n" + "=" * 80)
    print("STEP 2: Deleting data (respecting foreign key constraints)")
    print("=" * 80)

    # Delete in correct order (child tables first)
    tables_to_clear = [
        ('account', 'Better Auth - user accounts'),
        ('session', 'Better Auth - user sessions'),
        ('verification', 'Better Auth - verification tokens'),
        ('jwks', 'Better Auth - JSON Web Key Set'),
        ('"user"', 'Better Auth - users table'),
        ('tasks', 'Backend - tasks'),
        ('users', 'Backend - users'),
    ]

    for table, description in tables_to_clear:
        cur.execute(f"DELETE FROM {table}")
        deleted = cur.rowcount
        print(f"  [OK] {description} ({table}): {deleted} rows deleted")

    print("\n" + "=" * 80)
    print("STEP 3: Resetting sequences")
    print("=" * 80)

    # Reset sequences
    cur.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_class
                WHERE relname = 'tasks_id_seq'
                AND relkind = 'S'
            ) THEN
                ALTER SEQUENCE tasks_id_seq RESTART WITH 1;
                RAISE NOTICE 'Reset tasks_id_seq to 1';
            END IF;
        END $$;
    """)
    print("  [OK] Reset tasks_id_seq to 1 (if exists)")

    # Commit the transaction
    conn.commit()

    print("\n" + "=" * 80)
    print("STEP 4: Final Verification")
    print("=" * 80)

    # Verify final state
    cur.execute("""
        SELECT
            'account' AS table_name,
            COUNT(*) AS row_count
        FROM account
        UNION ALL
        SELECT 'session', COUNT(*) FROM session
        UNION ALL
        SELECT 'verification', COUNT(*) FROM verification
        UNION ALL
        SELECT 'jwks', COUNT(*) FROM jwks
        UNION ALL
        SELECT 'user', COUNT(*) FROM "user"
        UNION ALL
        SELECT 'tasks', COUNT(*) FROM tasks
        UNION ALL
        SELECT 'users', COUNT(*) FROM users;
    """)

    after_counts = cur.fetchall()
    print("\nAFTER RESET - Row Counts:")
    all_empty = True
    for table, count in after_counts:
        status_icon = "[OK]" if count == 0 else "[WARN]"
        print(f"  {status_icon} {table}: {count} rows")
        if count != 0:
            all_empty = False

    print("\n" + "=" * 80)
    if all_empty:
        print("SUCCESS: All authentication tables have been cleared!")
        print("=" * 80)
        print("\nNext Steps:")
        print("  1. Restart your backend server (if running)")
        print("  2. Restart your frontend dev server (if running)")
        print("  3. Try signing up with a new account")
        print("  4. The authentication flow should now work correctly")
    else:
        print("WARNING: Some tables still contain data!")
        print("=" * 80)
        print("\nThis may indicate foreign key constraint issues.")
        print("Please check the database schema and retry.")

    cur.close()
    conn.close()

except psycopg2.Error as e:
    print(f"\n[ERROR] DATABASE ERROR: {e}")
    if 'conn' in locals():
        conn.rollback()
        conn.close()
    sys.exit(1)
except Exception as e:
    print(f"\n[ERROR] {e}")
    if 'conn' in locals():
        conn.rollback()
        conn.close()
    sys.exit(1)
