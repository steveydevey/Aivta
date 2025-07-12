# Aivta - AI Agent Text Game Research Project

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/your-username/aivta)
[![Docker](https://img.shields.io/badge/docker-supported-blue)](https://www.docker.com/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Aivta (AI Avatar) is a research project that builds a Docker Compose stack with an AI agent that coordinates input/output mapping between an LLM and a text-based game. The goal is to enable the LLM to play the game to completion and map its path through the game.

## 🏗️ Architecture Overview

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   LLM Service       │    │   AI Agent          │    │   Text Game         │
│   (OpenAI/Local)    │◄──►│   (Coordinator)     │◄──►│   (Adventure Game)  │
│                     │    │                     │    │                     │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
           │                          │                          │
           │                          │                          │
           ▼                          ▼                          ▼
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   API Interface     │    │   Game State DB     │    │   Game Logs         │
│                     │    │   (Path Mapping)    │    │                     │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Git
- Python 3.11+ (for local development)

### Setup

1. **Clone the repository:**
```bash
git clone https://github.com/your-username/aivta.git
cd aivta
```

2. **Run the setup script:**
```bash
./scripts/setup.sh
```

3. **Configure environment variables:**
```bash
cp .env.example .env
# Edit .env with your configuration (especially OPENAI_API_KEY)
```

4. **Start the services:**
```bash
docker-compose up -d
```

5. **Verify the setup:**
```bash
# Check service health
curl http://localhost:8000/health  # AI Agent
curl http://localhost:8080/health  # Text Game

# View API documentation
open http://localhost:8000/docs    # AI Agent API
open http://localhost:8080/docs    # Text Game API
```

## 🎮 Usage

### Creating a Game Session

```bash
# Create a new game session
curl -X POST "http://localhost:8000/sessions" \
  -H "Content-Type: application/json" \
  -d '{"game_type": "adventure"}'
```

### Manual Game Control

```bash
# Execute a command in the game
curl -X POST "http://localhost:8000/sessions/{session_id}/actions" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id",
    "action": "look around",
    "context": "exploring the game world"
  }'
```

### Autonomous AI Gameplay

```bash
# Start autonomous gameplay
curl -X POST "http://localhost:8000/sessions/{session_id}/play"
```

### Monitoring Progress

```bash
# Get game path
curl "http://localhost:8000/sessions/{session_id}/path"

# Get agent statistics
curl "http://localhost:8000/stats"
```

## 📁 Project Structure

```
aivta/
├── docker-compose.yml          # Main orchestration file
├── .env                        # Environment configuration
├── services/
│   ├── ai-agent/              # AI Agent service (Python/FastAPI)
│   │   ├── main.py            # FastAPI application
│   │   ├── core/              # Core modules
│   │   ├── Dockerfile         # Docker configuration
│   │   └── requirements.txt   # Python dependencies
│   ├── text-game/             # Text game container
│   │   ├── main.py            # Game service
│   │   ├── game_engine.py     # Game logic
│   │   ├── Dockerfile         # Docker configuration
│   │   └── requirements.txt   # Python dependencies
│   └── database/              # PostgreSQL setup
│       └── init.sql           # Database schema
├── tests/                     # Test suites
│   ├── test_ai_agent.py       # AI Agent tests
│   ├── test_text_game.py      # Text Game tests
│   ├── conftest.py            # Test configuration
│   └── requirements.txt       # Test dependencies
├── scripts/                   # Utility scripts
│   ├── setup.sh               # Setup script
│   ├── test.sh                # Test runner
│   └── deploy.sh              # Deployment script
├── config/                    # Configuration files
│   └── settings.yaml          # Application settings
├── docs/                      # Documentation
└── README.md                  # This file
```

## 🛠️ Development

### Local Development Setup

1. **Install dependencies:**
```bash
# AI Agent service
cd services/ai-agent
pip install -r requirements.txt

# Text Game service
cd ../text-game
pip install -r requirements.txt

# Test dependencies
cd ../../
pip install -r tests/requirements.txt
```

2. **Run services locally:**
```bash
# Start database
docker-compose up -d database

# Run AI Agent
cd services/ai-agent
python main.py

# Run Text Game (in another terminal)
cd services/text-game
python main.py
```

### Running Tests

```bash
# Run all tests
./scripts/test.sh

# Run only unit tests
./scripts/test.sh --unit-only

# Run with coverage
./scripts/test.sh --coverage

# Run specific test file
python -m pytest tests/test_ai_agent.py -v
```

### Code Quality

```bash
# Format code
black services/

# Check linting
flake8 services/

# Type checking
mypy services/
```

## 🔧 Configuration

### Environment Variables

Key environment variables (set in `.env`):

```bash
# Database
DATABASE_URL=postgresql://aivta_user:aivta_password@database:5432/aivta

# LLM Configuration
OPENAI_API_KEY=your_openai_api_key_here
OLLAMA_HOST=http://ollama:11434

# Service Configuration
LOG_LEVEL=INFO
DEBUG=false
```

### Game Configuration

Modify `config/settings.yaml` for game-specific settings:

```yaml
text_game:
  game_type: "adventure"
  max_moves: 1000
  save_interval: 300

llm:
  model: "gpt-3.5-turbo"
  temperature: 0.7
  max_tokens: 1000
```

## 🎯 Game Features

### Adventure Game

The included text adventure game features:

- **Multiple Rooms**: Forest clearing, cave system, treasure room
- **Items**: Collectible items with different properties
- **Inventory System**: Pick up, drop, and use items
- **Scoring**: Points for exploration and item collection
- **Save/Load**: Persistent game state
- **Victory Condition**: Reach the forest exit

### AI Agent Capabilities

- **Game State Tracking**: Monitors all game states and transitions
- **Path Mapping**: Records and analyzes game paths
- **Decision Making**: Uses LLM to make intelligent game decisions
- **Error Recovery**: Handles invalid commands and game errors
- **Performance Metrics**: Tracks success rates and efficiency

## 📊 Research Features

### Path Mapping

The system tracks and analyzes:
- Complete game paths from start to finish
- Decision trees for different strategies
- Success rates for different approaches
- Exploration coverage metrics

### Data Collection

All interactions are logged to the database:
- Game states and transitions
- LLM interactions and decisions
- Performance metrics
- Error patterns and recovery

### Analytics

Use the database to analyze:
- Game completion rates
- Most efficient paths
- Common failure points
- LLM decision patterns

## 🐳 Docker Services

### AI Agent Service
- **Port**: 8000
- **Health Check**: `/health`
- **API Docs**: `/docs`

### Text Game Service
- **Port**: 8080
- **Health Check**: `/health`
- **API Docs**: `/docs`

### Database Service
- **Port**: 5432
- **Database**: `aivta`
- **User**: `aivta_user`

### Optional Services

#### Ollama (Local LLM)
```bash
# Start with local LLM
docker-compose --profile local-llm up -d
```

#### Web UI (Monitoring)
```bash
# Start with monitoring
docker-compose --profile monitoring up -d
```

## 📈 Monitoring

### Health Checks

All services include health check endpoints:

```bash
# Check all services
curl http://localhost:8000/health
curl http://localhost:8080/health
```

### Logs

View service logs:

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f ai-agent
```

### Database Queries

Connect to the database:

```bash
# Access database
docker-compose exec database psql -U aivta_user -d aivta

# Sample queries
SELECT * FROM game_sessions WHERE status = 'active';
SELECT * FROM game_paths WHERE success = true;
```

## 🚀 Deployment

### Development Deployment

```bash
./scripts/deploy.sh
```

### Production Deployment

```bash
./scripts/deploy.sh --environment production --build-fresh
```

### Rollback

```bash
./scripts/deploy.sh --rollback
```

## 🧪 Testing

### Test Categories

- **Unit Tests**: Test individual components
- **Integration Tests**: Test service interactions
- **End-to-End Tests**: Test complete workflows

### Test Commands

```bash
# Run all tests
./scripts/test.sh

# Run specific test categories
./scripts/test.sh --unit-only
./scripts/test.sh --integration-only

# Run with coverage
./scripts/test.sh --coverage
```

## 📋 API Reference

### AI Agent API

#### Create Session
```http
POST /sessions
Content-Type: application/json

{
  "game_type": "adventure"
}
```

#### Execute Action
```http
POST /sessions/{session_id}/actions
Content-Type: application/json

{
  "session_id": "uuid",
  "action": "go north",
  "context": "exploring"
}
```

#### Get Game Path
```http
GET /sessions/{session_id}/path
```

### Text Game API

#### Create Game Session
```http
POST /sessions
```

#### Execute Command
```http
POST /sessions/{session_id}/commands
Content-Type: application/json

{
  "session_id": "uuid",
  "command": "look around"
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for the GPT API
- FastAPI for the web framework
- Docker for containerization
- PostgreSQL for the database

## 🔗 Links

- [Project Documentation](docs/)
- [API Documentation](http://localhost:8000/docs)
- [Issue Tracker](https://github.com/your-username/aivta/issues)

---

**Note**: This is a research project. The AI agent's performance will vary based on the LLM used and the complexity of the game scenarios.