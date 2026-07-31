-- Migration: Add password column to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS password TEXT;

-- Migration: Create push_subscriptions table
CREATE TABLE IF NOT EXISTS push_subscriptions (
    user_id UUID PRIMARY KEY REFERENCES users(id),
    endpoint TEXT NOT NULL,
    p256dh TEXT NOT NULL,
    auth TEXT NOT NULL
);
