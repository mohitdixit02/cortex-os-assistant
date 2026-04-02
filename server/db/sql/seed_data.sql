-- Dummy seed data for integration testing.
-- Safe to run after create_tables.sql.

INSERT INTO users (
    user_id, google_id, email, full_name, phone_number, profile_picture, created_at, updated_at, deleted_at
) VALUES (
    '11111111-1111-1111-1111-111111111111',
    'google-oauth-sub-001',
    'alice@example.com',
    'Alice Johnson',
    '+15550001111',
    'https://cdn.example.com/profiles/alice.jpg',
    NOW(),
    NOW(),
    NULL
)
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO chat_sessions (
    session_id, user_id, summary, created_at, updated_at
) VALUES (
    '22222222-2222-2222-2222-222222222222',
    '11111111-1111-1111-1111-111111111111',
    'Discussed travel plans and reminder setup.',
    NOW(),
    NOW()
)
ON CONFLICT (session_id) DO NOTHING;

INSERT INTO messages (
    message_id, session_id, user_id, content, role, ai_client, is_tool_used, tool_id, embedding, created_at
) VALUES
(
    '33333333-3333-3333-3333-333333333331',
    '22222222-2222-2222-2222-222222222222',
    '11111111-1111-1111-1111-111111111111',
    'Set a reminder for tomorrow at 9 AM.',
    'USER',
    NULL,
    FALSE,
    NULL,
    NULL,
    NOW()
),
(
    '33333333-3333-3333-3333-333333333332',
    '22222222-2222-2222-2222-222222222222',
    '11111111-1111-1111-1111-111111111111',
    'Sure, I can set that reminder for you.',
    'AI',
    'VOICE_CLIENT',
    TRUE,
    'send_whatsapp',
    NULL,
    NOW()
)
ON CONFLICT (message_id) DO NOTHING;

INSERT INTO user_short_term_memory (
    stm_id, user_id, session_id, stm_summary, session_preferences, created_at, updated_at
) VALUES (
    '44444444-4444-4444-4444-444444444444',
    '11111111-1111-1111-1111-111111111111',
    '22222222-2222-2222-2222-222222222222',
    'User asked for schedule support and reminder automation.',
    '{"tone":"concise","response_style":"actionable"}'::jsonb,
    NOW(),
    NOW()
)
ON CONFLICT (stm_id) DO NOTHING;

INSERT INTO user_emotional_profiles (
    profile_id, user_id, session_id, mood_type, time_behavior,
    emotional_level, logical_level, social_level, context_summary, created_at
) VALUES (
    '55555555-5555-5555-5555-555555555555',
    '11111111-1111-1111-1111-111111111111',
    '22222222-2222-2222-2222-222222222222',
    'Focused',
    'MORNING',
    6,
    8,
    5,
    'User prefers efficient responses in the morning and minimal chit-chat.',
    NOW()
)
ON CONFLICT (profile_id) DO NOTHING;

INSERT INTO user_knowledge_base (
    trait_id, user_id, category, strictness, content, is_active, embedding, created_at, updated_at
) VALUES
(
    '66666666-6666-6666-6666-666666666661',
    '11111111-1111-1111-1111-111111111111',
    'LIKE',
    'SHOULD',
    'Prefers morning reminders and clear timeline summaries.',
    TRUE,
    NULL,
    NOW(),
    NOW()
),
(
    '66666666-6666-6666-6666-666666666662',
    '11111111-1111-1111-1111-111111111111',
    'DISLIKE',
    'MUST',
    'Does not like interruptions during focused work blocks.',
    TRUE,
    NULL,
    NOW(),
    NOW()
)
ON CONFLICT (trait_id) DO NOTHING;

INSERT INTO tools (
    tool_id, tool_name, tool_description, is_active, created_at, updated_at, deleted_at
) VALUES
(
    '77777777-7777-7777-7777-777777777771',
    'send_whatsapp',
    'Send a WhatsApp notification to the user with a message payload.',
    TRUE,
    NOW(),
    NOW(),
    NULL
),
(
    '77777777-7777-7777-7777-777777777772',
    'create_reminder',
    'Create a dated reminder item for the user calendar.',
    TRUE,
    NOW(),
    NOW(),
    NULL
)
ON CONFLICT (tool_id) DO NOTHING;

INSERT INTO tasks (
    task_id, message_id, tool_id, task_name, status, payload, status_response, task_metadata, created_at, updated_at
) VALUES
(
    '88888888-8888-8888-8888-888888888881',
    '33333333-3333-3333-3333-333333333332',
    '77777777-7777-7777-7777-777777777772',
    'TextResponseTask',
    'COMPLETED',
    '{"query":"Set a reminder for tomorrow at 9 AM"}'::jsonb,
    '{"response":"Reminder scheduled for tomorrow at 9 AM"}'::jsonb,
    '{"retry_count":0,"execution_time_ms":1200}'::jsonb,
    NOW(),
    NOW()
),
(
    '88888888-8888-8888-8888-888888888882',
    '33333333-3333-3333-3333-333333333332',
    '77777777-7777-7777-7777-777777777771',
    'NotifyUserTask',
    'QUEUED',
    '{"number":"+15550001111","text":"Your reminder is ready"}'::jsonb,
    NULL,
    '{"retry_count":0}'::jsonb,
    NOW(),
    NOW()
)
ON CONFLICT (task_id) DO NOTHING;
