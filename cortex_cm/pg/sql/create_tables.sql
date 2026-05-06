-- PostgreSQL DDL generated from SQLModel architecture
-- Requires pgvector extension for embedding columns.

CREATE EXTENSION IF NOT EXISTS vector;

DO $$ BEGIN
    CREATE TYPE role_type AS ENUM ('USER', 'AI');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE ai_client_type AS ENUM ('VOICE_CLIENT', 'CORTEX_MAIN_CLIENT');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE preference_level AS ENUM ('MUST', 'SHOULD', 'CAN', 'CANNOT');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE time_of_day AS ENUM ('MORNING', 'AFTERNOON', 'EVENING', 'NIGHT');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE task_status AS ENUM ('INITIALIZED', 'QUEUED', 'PROCESSING', 'COMPLETED', 'FAILED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE event_status AS ENUM ('CREATED', 'QUEUED', 'DONE', 'FAILED', 'CANCELLED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE task_owner AS ENUM ('VOICE_CLIENT', 'EVENT_TOOL', 'OTHER');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY,
    google_id VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(320) NOT NULL UNIQUE,
    full_name VARCHAR(255) NOT NULL,
    profile_picture VARCHAR(1024),
    google_refresh_token TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    deleted_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    summary VARCHAR(2000),
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    message_id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    role role_type NOT NULL,
    ai_client ai_client_type,
    is_summarized BOOLEAN NOT NULL DEFAULT FALSE,
    is_tool_used BOOLEAN NOT NULL DEFAULT FALSE,
    tool_id VARCHAR(255),
    embedding VECTOR,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS user_short_term_memory (
    stm_id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    stm_summary TEXT NOT NULL,
    session_preferences JSONB,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS user_emotional_profiles (
    profile_id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    mood_type VARCHAR(64) NOT NULL,
    time_behavior time_of_day NOT NULL,
    emotional_level INTEGER NOT NULL,
    logical_level INTEGER NOT NULL,
    social_level INTEGER NOT NULL,
    context_summary TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT ck_emotional_level_1_10 CHECK (emotional_level >= 1 AND emotional_level <= 10),
    CONSTRAINT ck_logical_level_1_10 CHECK (logical_level >= 1 AND logical_level <= 10),
    CONSTRAINT ck_social_level_1_10 CHECK (social_level >= 1 AND social_level <= 10)
);

CREATE TABLE IF NOT EXISTS user_knowledge_base (
    trait_id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    strictness preference_level,
    content TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    embedding VECTOR,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS tools (
    tool_id UUID PRIMARY KEY,
    tool_name VARCHAR(255) NOT NULL UNIQUE,
    tool_description TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    deleted_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS user_tool_subscriptions (
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    tool_id UUID NOT NULL REFERENCES tools(tool_id) ON DELETE CASCADE,
    is_subscribed BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (user_id, tool_id)
);

CREATE TABLE IF NOT EXISTS tasks (
    task_id UUID PRIMARY KEY,
    message_id UUID NOT NULL REFERENCES messages(message_id) ON DELETE CASCADE,
    tool_id UUID REFERENCES tools(tool_id) ON DELETE RESTRICT,
    task_name VARCHAR(255) NOT NULL,
    task_description TEXT,
    status task_status NOT NULL,
    task_owner task_owner NOT NULL DEFAULT 'OTHER',
    payload JSONB NOT NULL,
    status_response JSONB,
    task_metadata JSONB,
    embedding VECTOR,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS user_events (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    event_info TEXT,
    event_description TEXT,
    embedding VECTOR,
    trigger_time TIMESTAMPTZ NOT NULL,
    status event_status NOT NULL DEFAULT 'CREATED',
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_users_google_id ON users(google_id);
CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);
CREATE INDEX IF NOT EXISTS ix_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS ix_messages_session_id ON messages(session_id);
CREATE INDEX IF NOT EXISTS ix_messages_user_id ON messages(user_id);
CREATE INDEX IF NOT EXISTS ix_messages_role ON messages(role);
CREATE INDEX IF NOT EXISTS ix_messages_ai_client ON messages(ai_client);
CREATE INDEX IF NOT EXISTS ix_messages_created_at ON messages(created_at);
CREATE INDEX IF NOT EXISTS ix_messages_session_created ON messages(session_id, created_at);
CREATE INDEX IF NOT EXISTS ix_user_short_term_memory_user_id ON user_short_term_memory(user_id);
CREATE INDEX IF NOT EXISTS ix_user_short_term_memory_session_id ON user_short_term_memory(session_id);
CREATE INDEX IF NOT EXISTS ix_user_emotional_profiles_user_id ON user_emotional_profiles(user_id);
CREATE INDEX IF NOT EXISTS ix_user_emotional_profiles_session_id ON user_emotional_profiles(session_id);
CREATE INDEX IF NOT EXISTS ix_user_knowledge_base_user_id ON user_knowledge_base(user_id);
CREATE INDEX IF NOT EXISTS ix_user_knowledge_base_strictness ON user_knowledge_base(strictness);
CREATE INDEX IF NOT EXISTS ix_user_knowledge_base_is_active ON user_knowledge_base(is_active);
CREATE INDEX IF NOT EXISTS ix_tools_tool_name ON tools(tool_name);
CREATE INDEX IF NOT EXISTS ix_tools_is_active ON tools(is_active);
CREATE INDEX IF NOT EXISTS ix_tasks_message_id ON tasks(message_id);
CREATE INDEX IF NOT EXISTS ix_tasks_tool_id ON tasks(tool_id);
CREATE INDEX IF NOT EXISTS ix_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS ix_tasks_status_updated ON tasks(status, updated_at);
CREATE INDEX IF NOT EXISTS ix_messages_is_summarized ON messages (is_summarized);
CREATE INDEX IF NOT EXISTS idx_events_trigger_time ON user_events(trigger_time) WHERE status = 'CREATED';
