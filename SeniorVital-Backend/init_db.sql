-- Extensión para UUID
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Tabla users (igual)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('senior', 'caregiver', 'admin')),
    profile JSONB NOT NULL,
    linked_senior_id UUID NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tabla tracking (igual)
CREATE TABLE tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    completed_at TIMESTAMP NOT NULL,
    exercise_id TEXT NOT NULL,
    sets INT NOT NULL,
    reps INT NOT NULL,
    rpe INT CHECK (rpe BETWEEN 1 AND 10),
    felt_difficulty TEXT
);

-- Tabla habits (igual)
CREATE TABLE habits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    water_glasses INT,
    sleep_hours FLOAT,
    UNIQUE(user_id, date)
);

-- Tabla routines (rutinas generadas)
CREATE TABLE routines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    exercises JSONB NOT NULL,
    warmup JSONB,
    active BOOLEAN DEFAULT true
);

-- Tabla projections (insights del agente preventivo)
CREATE TABLE projections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    week_start DATE NOT NULL,
    insight_text TEXT,
    estimated_level INT
);

-- Tabla exercises (catálogo)
CREATE TABLE exercises (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    level INT CHECK (level BETWEEN 1 AND 4),
    contraindications TEXT[],
    video_url TEXT   -- ahora apunta a ruta local, ej. /storage/videos/abc.mp4
);

-- NUEVA TABLA: Cola de eventos asíncronos (reemplaza Redis Streams)
CREATE TABLE event_queue (
    id BIGSERIAL PRIMARY KEY,
    stream_name TEXT NOT NULL,        -- 'ejercicio-completado', 'fatiga-alta', etc.
    payload JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP
);

-- Índices para la cola de eventos
CREATE INDEX idx_event_queue_stream_processed ON event_queue(stream_name, processed, created_at);

-- Índices originales
CREATE INDEX idx_tracking_user_completed ON tracking(user_id, completed_at DESC);
CREATE INDEX idx_tracking_exercise ON tracking(exercise_id);
CREATE INDEX idx_habits_user_date ON habits(user_id, date);
CREATE INDEX idx_routines_user_date ON routines(user_id, date);
CREATE INDEX idx_projection_user_week ON projections(user_id, week_start);
CREATE INDEX idx_exercises_level ON exercises(level);
CREATE INDEX idx_exercises_contraindications ON exercises USING GIN(contraindications);
CREATE INDEX idx_users_role ON users(role);