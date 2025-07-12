-- Aivta Database Initialization Script
-- This script creates the necessary tables for the AI agent game research project

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Game sessions table
CREATE TABLE IF NOT EXISTS game_sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_type VARCHAR(50) NOT NULL DEFAULT 'adventure',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    player_score INTEGER DEFAULT 0,
    total_moves INTEGER DEFAULT 0,
    victory BOOLEAN DEFAULT FALSE,
    current_room VARCHAR(100),
    metadata JSONB DEFAULT '{}'
);

-- Game states table - tracks individual game state snapshots
CREATE TABLE IF NOT EXISTS game_states (
    state_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES game_sessions(session_id) ON DELETE CASCADE,
    move_number INTEGER NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    room_name VARCHAR(100) NOT NULL,
    room_description TEXT,
    player_inventory JSONB DEFAULT '[]',
    available_items JSONB DEFAULT '[]',
    available_exits JSONB DEFAULT '{}',
    player_score INTEGER DEFAULT 0,
    game_over BOOLEAN DEFAULT FALSE,
    victory BOOLEAN DEFAULT FALSE
);

-- Game actions table - tracks all actions taken
CREATE TABLE IF NOT EXISTS game_actions (
    action_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES game_sessions(session_id) ON DELETE CASCADE,
    move_number INTEGER NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    command TEXT NOT NULL,
    response TEXT,
    success BOOLEAN DEFAULT TRUE,
    previous_state_id UUID REFERENCES game_states(state_id),
    resulting_state_id UUID REFERENCES game_states(state_id)
);

-- LLM interactions table - tracks AI agent decisions
CREATE TABLE IF NOT EXISTS llm_interactions (
    interaction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES game_sessions(session_id) ON DELETE CASCADE,
    action_id UUID REFERENCES game_actions(action_id),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    prompt TEXT NOT NULL,
    response TEXT NOT NULL,
    model_name VARCHAR(100),
    tokens_used INTEGER,
    processing_time_ms INTEGER,
    confidence_score REAL,
    metadata JSONB DEFAULT '{}'
);

-- Path mapping table - maps paths through the game
CREATE TABLE IF NOT EXISTS game_paths (
    path_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES game_sessions(session_id) ON DELETE CASCADE,
    path_sequence INTEGER[] NOT NULL, -- Array of move numbers forming the path
    start_room VARCHAR(100) NOT NULL,
    end_room VARCHAR(100) NOT NULL,
    total_moves INTEGER NOT NULL,
    success BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    path_hash VARCHAR(64) UNIQUE -- Hash of the path for quick lookup
);

-- Room exploration table - tracks room discovery and visits
CREATE TABLE IF NOT EXISTS room_explorations (
    exploration_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES game_sessions(session_id) ON DELETE CASCADE,
    room_name VARCHAR(100) NOT NULL,
    first_visit_move INTEGER NOT NULL,
    visit_count INTEGER DEFAULT 1,
    items_found JSONB DEFAULT '[]',
    exits_discovered JSONB DEFAULT '{}',
    fully_explored BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Game statistics table - aggregate statistics for analysis
CREATE TABLE IF NOT EXISTS game_statistics (
    stat_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES game_sessions(session_id) ON DELETE CASCADE,
    total_rooms_visited INTEGER DEFAULT 0,
    total_items_collected INTEGER DEFAULT 0,
    total_commands_executed INTEGER DEFAULT 0,
    average_response_time_ms REAL DEFAULT 0,
    completion_rate REAL DEFAULT 0,
    efficiency_score REAL DEFAULT 0,
    exploration_coverage REAL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_game_sessions_status ON game_sessions(status);
CREATE INDEX IF NOT EXISTS idx_game_sessions_created_at ON game_sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_game_sessions_game_type ON game_sessions(game_type);

CREATE INDEX IF NOT EXISTS idx_game_states_session_id ON game_states(session_id);
CREATE INDEX IF NOT EXISTS idx_game_states_move_number ON game_states(move_number);
CREATE INDEX IF NOT EXISTS idx_game_states_timestamp ON game_states(timestamp);

CREATE INDEX IF NOT EXISTS idx_game_actions_session_id ON game_actions(session_id);
CREATE INDEX IF NOT EXISTS idx_game_actions_move_number ON game_actions(move_number);
CREATE INDEX IF NOT EXISTS idx_game_actions_timestamp ON game_actions(timestamp);

CREATE INDEX IF NOT EXISTS idx_llm_interactions_session_id ON llm_interactions(session_id);
CREATE INDEX IF NOT EXISTS idx_llm_interactions_timestamp ON llm_interactions(timestamp);

CREATE INDEX IF NOT EXISTS idx_game_paths_session_id ON game_paths(session_id);
CREATE INDEX IF NOT EXISTS idx_game_paths_path_hash ON game_paths(path_hash);

CREATE INDEX IF NOT EXISTS idx_room_explorations_session_id ON room_explorations(session_id);
CREATE INDEX IF NOT EXISTS idx_room_explorations_room_name ON room_explorations(room_name);

-- Create triggers for updating timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_game_sessions_updated_at 
    BEFORE UPDATE ON game_sessions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_game_statistics_updated_at 
    BEFORE UPDATE ON game_statistics 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create views for common queries
CREATE OR REPLACE VIEW session_summary AS
SELECT 
    gs.session_id,
    gs.game_type,
    gs.status,
    gs.created_at,
    gs.completed_at,
    gs.player_score,
    gs.total_moves,
    gs.victory,
    gs.current_room,
    stat.total_rooms_visited,
    stat.total_items_collected,
    stat.exploration_coverage,
    stat.efficiency_score
FROM game_sessions gs
LEFT JOIN game_statistics stat ON gs.session_id = stat.session_id;

CREATE OR REPLACE VIEW active_sessions AS
SELECT * FROM session_summary WHERE status = 'active';

CREATE OR REPLACE VIEW completed_sessions AS
SELECT * FROM session_summary WHERE status IN ('completed', 'won', 'failed');

-- Insert initial data (if needed)
-- This can be used to insert reference data, configuration, etc.

-- Grant permissions (adjust as needed for your security requirements)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO aivta_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO aivta_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO aivta_user;

-- Create indexes for JSONB columns
CREATE INDEX IF NOT EXISTS idx_game_sessions_metadata ON game_sessions USING GIN(metadata);
CREATE INDEX IF NOT EXISTS idx_game_states_inventory ON game_states USING GIN(player_inventory);
CREATE INDEX IF NOT EXISTS idx_game_states_items ON game_states USING GIN(available_items);
CREATE INDEX IF NOT EXISTS idx_game_states_exits ON game_states USING GIN(available_exits);
CREATE INDEX IF NOT EXISTS idx_llm_interactions_metadata ON llm_interactions USING GIN(metadata);
CREATE INDEX IF NOT EXISTS idx_room_explorations_items ON room_explorations USING GIN(items_found);
CREATE INDEX IF NOT EXISTS idx_room_explorations_exits ON room_explorations USING GIN(exits_discovered);

-- Log the completion of the initialization
INSERT INTO game_sessions (session_id, game_type, status, metadata) 
VALUES (
    uuid_generate_v4(),
    'system',
    'initialized',
    '{"type": "database_init", "timestamp": "' || CURRENT_TIMESTAMP || '"}'
) ON CONFLICT DO NOTHING;