-- Migration: Create Conversation and Message tables for Phase 3 AI Chatbot
-- Author: Backend Infrastructure Team
-- Date: 2026-02-09
-- Depends: init_db.sql (users table must exist)

-- Conversation table: One active conversation per user
CREATE TABLE IF NOT EXISTS conversation (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL DEFAULT 'Task Assistant',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Message table: Chat messages within a conversation
CREATE TABLE IF NOT EXISTS message (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversation(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    metadata_json TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_conversation_user_id ON conversation(user_id);
CREATE INDEX IF NOT EXISTS idx_message_conversation_id ON message(conversation_id);
CREATE INDEX IF NOT EXISTS idx_message_created_at ON message(conversation_id, created_at DESC);

-- Trigger to auto-update conversation.updated_at
DROP TRIGGER IF EXISTS update_conversation_updated_at ON conversation;
CREATE TRIGGER update_conversation_updated_at
    BEFORE UPDATE ON conversation
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE conversation IS 'Chat conversation threads between users and AI assistant';
COMMENT ON TABLE message IS 'Individual messages within a conversation (user or assistant role)';
COMMENT ON COLUMN message.metadata_json IS 'JSON string storing tool_calls, action type, and reasoning traces';
COMMENT ON COLUMN message.role IS 'Message sender: user (human) or assistant (AI)';
