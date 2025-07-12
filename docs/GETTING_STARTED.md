# Getting Started with Aivta

This guide will help you get Aivta up and running quickly.

## Prerequisites

Before you start, make sure you have:

- **Docker** and **Docker Compose** installed
- **Git** for cloning the repository
- **Python 3.11+** (optional, for local development)
- **OpenAI API Key** (if using OpenAI, or set up Ollama for local LLM)

## Step 1: Clone and Setup

1. **Clone the repository:**
```bash
git clone https://github.com/your-username/aivta.git
cd aivta
```

2. **Run the automated setup:**
```bash
./scripts/setup.sh
```

This script will:
- Check Docker installation
- Create necessary directories
- Build Docker images
- Initialize the database
- Set up configuration files

## Step 2: Environment Configuration

1. **Copy the environment template:**
```bash
cp .env.example .env
```

2. **Edit the `.env` file:**
```bash
# Required: Add your OpenAI API key
OPENAI_API_KEY=sk-your-openai-api-key-here

# Optional: Customize other settings
LOG_LEVEL=INFO
DEBUG=false
```

## Step 3: Start the Services

1. **Start all services:**
```bash
docker-compose up -d
```

2. **Verify services are running:**
```bash
# Check service status
docker-compose ps

# Test health endpoints
curl http://localhost:8000/health  # AI Agent
curl http://localhost:8080/health  # Text Game
```

## Step 4: First Game Session

1. **Create a new game session:**
```bash
curl -X POST "http://localhost:8000/sessions" \
  -H "Content-Type: application/json" \
  -d '{"game_type": "adventure"}'
```

Save the returned `session_id` for the next steps.

2. **Execute your first command:**
```bash
curl -X POST "http://localhost:8000/sessions/YOUR_SESSION_ID/actions" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "YOUR_SESSION_ID",
    "action": "look around",
    "context": "starting the game"
  }'
```

3. **Start autonomous gameplay:**
```bash
curl -X POST "http://localhost:8000/sessions/YOUR_SESSION_ID/play"
```

## Step 5: Explore the APIs

1. **Open the API documentation:**
   - AI Agent API: http://localhost:8000/docs
   - Text Game API: http://localhost:8080/docs

2. **Try the interactive API:**
   - Use the Swagger UI to test endpoints
   - Create sessions and execute commands
   - Monitor game progress

## Step 6: Monitor Progress

1. **Check game statistics:**
```bash
curl http://localhost:8000/stats
```

2. **View game path:**
```bash
curl http://localhost:8000/sessions/YOUR_SESSION_ID/path
```

3. **View logs:**
```bash
docker-compose logs -f ai-agent
docker-compose logs -f text-game
```

## Common Issues and Solutions

### Services Won't Start
```bash
# Check if ports are in use
lsof -i :8000
lsof -i :8080
lsof -i :5432

# Restart services
docker-compose down
docker-compose up -d
```

### Database Connection Issues
```bash
# Check database status
docker-compose exec database pg_isready -U aivta_user -d aivta

# Restart database
docker-compose restart database
```

### LLM Connection Issues
```bash
# Check your API key
grep OPENAI_API_KEY .env

# Test LLM connection
curl http://localhost:8000/debug/llm
```

## Next Steps

1. **Experiment with different prompts and strategies**
2. **Analyze the game data in the database**
3. **Try different LLM models and settings**
4. **Extend the game with new rooms and items**
5. **Implement new research features**

## Getting Help

- Check the main [README.md](../README.md) for detailed documentation
- Look at the [API documentation](http://localhost:8000/docs)
- Review the [project structure](../README.md#project-structure)
- Check the [troubleshooting guide](TROUBLESHOOTING.md)

## Development Mode

If you want to develop and modify the code:

1. **Install Python dependencies:**
```bash
pip install -r services/ai-agent/requirements.txt
pip install -r services/text-game/requirements.txt
pip install -r tests/requirements.txt
```

2. **Run services locally:**
```bash
# Start database only
docker-compose up -d database

# Run AI Agent locally
cd services/ai-agent
python main.py

# Run Text Game locally (in another terminal)
cd services/text-game
python main.py
```

3. **Run tests:**
```bash
./scripts/test.sh
```

4. **Code formatting:**
```bash
black services/
flake8 services/
```

Happy experimenting with Aivta! 🎮🤖