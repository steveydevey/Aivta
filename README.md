# Aivta - AI Agent Text Game Research Project

## Project Overview

**Aivta** (AI Avatar) is a research project that builds a Docker Compose stack with an AI agent that coordinates input/output mapping between an LLM and a text-based game. The goal is to enable the LLM to play the game to completion and map its path through the game.

## Architecture

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   LLM Service       │    │   AI Agent          │    │   Text Game         │
│   (OpenAI/Local)    │◄──►│   (Coordinator)     │◄──►│   (Adventure Game)  │
│                     │    │                     │    │                     │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
           │                          │                          │
           │                          ▼                          ▼
           ▼                  ┌─────────────────────┐    ┌─────────────────────┐
┌─────────────────────┐      │   Game State DB     │    │   Game Logs         │
│   API Interface     │      │   (Path Mapping)    │    │                     │
└─────────────────────┘      └─────────────────────┘    └─────────────────────┘
```

## Services

### Core Services
- **AI Agent** (`services/ai-agent/`): Python FastAPI service that coordinates between LLM and game
- **Text Game** (`services/text-game/`): Simple text adventure game for testing
- **Database** (`services/database/`): PostgreSQL database for game state and path mapping
- **Web UI** (`services/web-ui/`): Monitoring interface for the system

### Optional Services
- **Ollama** (`services/ollama/`): Local LLM service for offline operation
- **Web UI** (`services/web-ui/`): Monitoring and debugging interface

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- Node.js 18+ (for web UI)

### 1. Clone and Setup
```bash
git clone <repository-url>
cd aivta
```

### 2. Environment Configuration
Create a `.env` file in the project root:
```bash
# OpenAI API Key (optional)
OPENAI_API_KEY=your_openai_api_key_here

# Logging level
LOG_LEVEL=INFO

# Ollama host (if using local LLM)
OLLAMA_HOST=http://ollama:11434
```

### 3. Start Services
```bash
# Start core services
docker-compose up -d

# Start with local LLM support
docker-compose --profile local-llm up -d

# Start with monitoring UI
docker-compose --profile monitoring up -d
```

### 4. Verify Services
```bash
# Check service health
curl http://localhost:8000/health    # AI Agent
curl http://localhost:8080/health    # Text Game
curl http://localhost:3000/api/health # Web UI
```

## Development

### Project Structure
```
aivta/
├── docker-compose.yml          # Main orchestration file
├── services/
│   ├── ai-agent/              # AI Agent service (Python/FastAPI)
│   ├── text-game/             # Text game container
│   ├── database/              # PostgreSQL database
│   └── web-ui/                # Web monitoring interface
├── tests/                     # Test suites
├── docs/                      # Project documentation
├── config/                    # Configuration files
└── scripts/                   # Utility scripts
```

### Running Tests

#### Install Test Dependencies
```bash
pip install -r requirements-test.txt
```

#### Run All Tests
```bash
pytest
```

#### Run Specific Test Categories
```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Tests with coverage report
pytest --cov=services/ai-agent --cov-report=html
```

#### Test Individual Services
```bash
# Test AI Agent
pytest tests/test_ai_agent.py

# Test Text Game
pytest tests/test_text_game.py

# Test Database
pytest tests/test_database.py
```

### Code Quality
```bash
# Format code
black services/ai-agent/

# Type checking
mypy services/ai-agent/

# Linting
flake8 services/ai-agent/
```

## API Documentation

### AI Agent Service (Port 8000)
- `GET /health` - Service health check
- `POST /game/session` - Create new game session
- `POST /game/action` - Execute game action
- `GET /game/session/{session_id}` - Get session status

### Text Game Service (Port 8080)
- `GET /health` - Service health check
- `GET /game/state` - Get current game state
- `POST /game/command` - Execute game command
- `POST /game/reset` - Reset game to initial state

### Web UI Service (Port 3000)
- `GET /api/health` - Service health check
- `GET /api/dashboard` - Main dashboard
- `GET /api/ai-agent` - AI Agent status
- `GET /api/text-game` - Text Game status

## Game Commands

The text game supports the following commands:
- `go <direction>` - Move in specified direction (north, south, east, west)
- `take <item>` - Pick up an item
- `look around` - Get current location description
- `inventory` - Show current inventory

## Database Schema

### Tables
- **game_sessions**: Game session tracking
- **game_states**: Game state snapshots
- **game_actions**: Actions taken by AI agent
- **path_mapping**: Complete path through the game

## Configuration

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `OPENAI_API_KEY`: OpenAI API key for LLM access
- `OLLAMA_HOST`: Ollama service host for local LLM
- `TEXT_GAME_HOST`: Text game service host
- `TEXT_GAME_PORT`: Text game service port
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

### Docker Compose Profiles
- **default**: Core services (AI Agent, Text Game, Database)
- **local-llm**: Includes Ollama for local LLM support
- **monitoring**: Includes Web UI for monitoring

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check service logs
docker-compose logs <service-name>

# Check service health
docker-compose ps
```

#### Database Connection Issues
```bash
# Verify database is running
docker-compose ps database

# Check database logs
docker-compose logs database
```

#### Test Failures
```bash
# Run tests with verbose output
pytest -v

# Run specific failing test
pytest tests/test_specific.py::test_function -v
```

## Contributing

### Development Workflow
1. Create feature branch from `main`
2. Implement changes with tests
3. Ensure all tests pass
4. Update documentation
5. Submit pull request

### Code Standards
- Python: PEP 8, type hints, docstrings
- Tests: pytest, comprehensive coverage
- Documentation: Clear and up-to-date

## Project Status

### Phase 1: Foundation Setup ✅
- [x] Project structure and Docker Compose configuration
- [x] Core service architectures
- [x] Testing and development infrastructure
- [x] Basic text game implementation

### Phase 2: Basic Game Integration 🚧
- [ ] AI agent core implementation
- [ ] LLM integration
- [ ] Game state tracking
- [ ] Basic path mapping

### Phase 3: Intelligent Game Playing 📋
- [ ] Game understanding and decision making
- [ ] Strategic thinking implementation
- [ ] Advanced path mapping

## License

MIT License - see LICENSE file for details.

## Contact

For questions or contributions, please open an issue or pull request on the project repository.