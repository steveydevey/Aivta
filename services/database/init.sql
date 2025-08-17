-- Aivta Database Initialization Script
-- Creates tables for game state tracking and path mapping

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Game sessions table
CREATE TABLE IF NOT EXISTS game_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    game_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Game states table
CREATE TABLE IF NOT EXISTS game_states (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES game_sessions(id) ON DELETE CASCADE,
    state_hash VARCHAR(255) NOT NULL,
    game_description TEXT NOT NULL,
    available_actions JSONB,
    inventory JSONB,
    location VARCHAR(255),
    score INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Game actions table
CREATE TABLE IF NOT EXISTS game_actions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES game_sessions(id) ON DELETE CASCADE,
    from_state_id UUID REFERENCES game_states(id),
    to_state_id UUID REFERENCES game_states(id),
    action VARCHAR(500) NOT NULL,
    llm_reasoning TEXT,
    success BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Path mapping table
CREATE TABLE IF NOT EXISTS path_mapping (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES game_sessions(id) ON DELETE CASCADE,
    path_sequence INTEGER NOT NULL,
    state_id UUID REFERENCES game_states(id),
    action_id UUID REFERENCES game_actions(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_game_sessions_session_id ON game_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_game_states_session_id ON game_states(session_id);
CREATE INDEX IF NOT EXISTS idx_game_states_state_hash ON game_states(state_hash);
CREATE INDEX IF NOT EXISTS idx_game_actions_session_id ON game_actions(session_id);
CREATE INDEX IF NOT EXISTS idx_path_mapping_session_id ON path_mapping(session_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for game_sessions table
CREATE TRIGGER update_game_sessions_updated_at 
    BEFORE UPDATE ON game_sessions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();