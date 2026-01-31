-- ============================================================================
-- NEON POSTGRESQL DATABASE RESET SCRIPT
-- ============================================================================
-- Purpose: Clear all authentication and user-related data while preserving schema
-- Updated: 2026-01-30
--
-- This script resets:
--   1. Better Auth tables: user, session, account, verification, jwks
--   2. Application tables: tasks
--
-- Foreign Key Relationships:
--   - account.userId -> user.id
--   - session.userId -> user.id
--   - tasks.user_id -> user.id
--
-- Deletion Order: Child tables first, then parent tables
-- ============================================================================

BEGIN;

-- Display current state before deletion
SELECT 'BEFORE RESET - Row Counts:' AS status;
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
SELECT 'tasks', COUNT(*) FROM tasks;

-- ============================================================================
-- STEP 1: Delete data from child tables (that reference user table)
-- ============================================================================

-- Delete from tasks table (references user.id)
DELETE FROM tasks;
SELECT 'Deleted all records from tasks table' AS status;

-- Delete from account table (references user.id)
DELETE FROM account;
SELECT 'Deleted all records from account table' AS status;

-- Delete from session table (references user.id)
DELETE FROM session;
SELECT 'Deleted all records from session table' AS status;

-- Delete from verification table (no foreign key, but auth-related)
DELETE FROM verification;
SELECT 'Deleted all records from verification table' AS status;

-- Delete from jwks table (no foreign key, but auth-related)
DELETE FROM jwks;
SELECT 'Deleted all records from jwks table' AS status;

-- ============================================================================
-- STEP 2: Delete data from parent table
-- ============================================================================

-- Delete from user table (parent table for account, session, tasks)
DELETE FROM "user";
SELECT 'Deleted all records from user table' AS status;

-- ============================================================================
-- STEP 3: Reset sequences
-- ============================================================================

-- Reset tasks table ID sequence (if exists)
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
    ELSE
        RAISE NOTICE 'Sequence tasks_id_seq does not exist';
    END IF;
END $$;

-- ============================================================================
-- STEP 4: Verification - Display final state
-- ============================================================================

SELECT 'AFTER RESET - Row Counts:' AS status;
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
SELECT 'tasks', COUNT(*) FROM tasks;

-- ============================================================================
-- STEP 5: Final verification query
-- ============================================================================

SELECT
    CASE
        WHEN (
            (SELECT COUNT(*) FROM account) = 0 AND
            (SELECT COUNT(*) FROM session) = 0 AND
            (SELECT COUNT(*) FROM verification) = 0 AND
            (SELECT COUNT(*) FROM jwks) = 0 AND
            (SELECT COUNT(*) FROM "user") = 0 AND
            (SELECT COUNT(*) FROM tasks) = 0
        ) THEN 'SUCCESS: All tables are empty'
        ELSE 'WARNING: Some tables still contain data'
    END AS reset_status;

COMMIT;

SELECT 'Database reset completed successfully!' AS final_status;
