-- ============================================================================
-- TASKS TABLE SCHEMA FOR NEON POSTGRESQL
-- ============================================================================
-- This script creates the tasks table with proper foreign key to Better Auth's
-- user table. Run this after Better Auth tables are created.
--
-- The user_id column is TEXT to match Better Auth's user.id format.
-- ============================================================================

-- Drop existing tasks table if it exists (with cascade to handle any references)
DROP TABLE IF EXISTS "tasks" CASCADE;

-- Create tasks table with foreign key to Better Auth's user table
CREATE TABLE "tasks" (
    "id" SERIAL PRIMARY KEY,
    "user_id" TEXT NOT NULL REFERENCES "user"("id") ON DELETE CASCADE,
    "title" VARCHAR(200) NOT NULL,
    "description" TEXT,
    "priority" VARCHAR(20) NOT NULL DEFAULT 'medium',
    "category" VARCHAR(50),
    "due_date" DATE,
    "completed" BOOLEAN NOT NULL DEFAULT FALSE,
    "created_at" TIMESTAMP NOT NULL DEFAULT NOW(),
    "updated_at" TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Constraint to ensure priority is one of the allowed values
    CONSTRAINT "tasks_priority_check" CHECK ("priority" IN ('low', 'medium', 'high'))
);

-- Create indexes for better query performance
CREATE INDEX "idx_tasks_user_id" ON "tasks"("user_id");
CREATE INDEX "idx_tasks_completed" ON "tasks"("completed");
CREATE INDEX "idx_tasks_priority" ON "tasks"("priority");
CREATE INDEX "idx_tasks_due_date" ON "tasks"("due_date");
CREATE INDEX "idx_tasks_created_at" ON "tasks"("created_at");

-- Composite index for common query patterns
CREATE INDEX "idx_tasks_user_completed" ON "tasks"("user_id", "completed");

-- Verify table creation
SELECT 'Tasks table created successfully!' AS status;

-- Show table structure
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'tasks'
ORDER BY ordinal_position;
