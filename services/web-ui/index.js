const express = require('express');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({ status: 'healthy', service: 'web-ui' });
});

// Main dashboard endpoint
app.get('/api/dashboard', (req, res) => {
  res.json({
    service: 'Aivta Web UI',
    status: 'running',
    endpoints: {
      ai_agent: '/api/ai-agent',
      text_game: '/api/text-game',
      database: '/api/database'
    }
  });
});

// AI Agent status endpoint
app.get('/api/ai-agent', async (req, res) => {
  try {
    const aiAgentHost = process.env.AI_AGENT_HOST || 'ai-agent';
    const aiAgentPort = process.env.AI_AGENT_PORT || 8000;
    
    // In a real implementation, this would make a request to the AI agent
    res.json({
      service: 'AI Agent',
      status: 'connected',
      host: aiAgentHost,
      port: aiAgentPort
    });
  } catch (error) {
    res.status(500).json({ error: 'Failed to connect to AI Agent' });
  }
});

// Text Game status endpoint
app.get('/api/text-game', async (req, res) => {
  try {
    res.json({
      service: 'Text Game',
      status: 'running',
      game_type: 'adventure'
    });
  } catch (error) {
    res.status(500).json({ error: 'Failed to get text game status' });
  }
});

// Database status endpoint
app.get('/api/database', async (req, res) => {
  try {
    res.json({
      service: 'Database',
      status: 'connected',
      type: 'PostgreSQL'
    });
  } catch (error) {
    res.status(500).json({ error: 'Failed to get database status' });
  }
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Aivta Web UI running on port ${PORT}`);
});