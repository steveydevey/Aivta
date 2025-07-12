#!/bin/bash

# Aivta Project Setup Script
# This script sets up the development environment for the Aivta project

set -e

echo "🚀 Setting up Aivta development environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_status "Docker and Docker Compose are installed"
}

# Create necessary directories
create_directories() {
    print_status "Creating project directories..."
    
    # Create logs directory
    mkdir -p logs
    
    # Create saves directory for games
    mkdir -p services/text-game/saves
    
    # Create config directory if it doesn't exist
    mkdir -p config
    
    # Create docs directory structure
    mkdir -p docs/api
    mkdir -p docs/architecture
    mkdir -p docs/research
    
    print_status "Directories created successfully"
}

# Set up environment file
setup_env() {
    print_status "Setting up environment configuration..."
    
    if [ ! -f .env ]; then
        print_warning ".env file not found. Please create one from .env.example"
        print_status "Copying .env.example to .env..."
        cp .env.example .env 2>/dev/null || cp .env .env.local 2>/dev/null || {
            print_warning "No .env.example found. Please create .env manually"
        }
    else
        print_status ".env file already exists"
    fi
}

# Build Docker images
build_images() {
    print_status "Building Docker images..."
    
    # Build all services
    docker-compose build --no-cache
    
    print_status "Docker images built successfully"
}

# Initialize database
init_database() {
    print_status "Initializing database..."
    
    # Start only the database service
    docker-compose up -d database
    
    # Wait for database to be ready
    print_status "Waiting for database to be ready..."
    sleep 10
    
    # Check if database is ready
    docker-compose exec database pg_isready -U aivta_user -d aivta || {
        print_error "Database failed to start properly"
        exit 1
    }
    
    print_status "Database initialized successfully"
}

# Run tests
run_tests() {
    print_status "Running test suite..."
    
    # Install test dependencies
    if [ -f tests/requirements.txt ]; then
        pip install -r tests/requirements.txt
    fi
    
    # Run tests
    python -m pytest tests/ -v --tb=short || {
        print_warning "Some tests failed, but continuing setup..."
    }
    
    print_status "Test suite completed"
}

# Create sample configuration
create_sample_config() {
    print_status "Creating sample configuration files..."
    
    # Create a sample game configuration
    cat > config/game_config.json << EOF
{
    "game_settings": {
        "max_moves": 1000,
        "save_interval": 300,
        "difficulty": "normal"
    },
    "world_settings": {
        "starting_room": "start",
        "victory_conditions": ["reach_forest_exit"],
        "scoring": {
            "exploration": 5,
            "item_collection": 10,
            "completion": 100
        }
    }
}
EOF
    
    print_status "Sample configuration created"
}

# Set up git hooks (if git is available)
setup_git_hooks() {
    if command -v git &> /dev/null && [ -d .git ]; then
        print_status "Setting up git hooks..."
        
        # Create pre-commit hook
        cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Pre-commit hook for code quality checks

echo "Running pre-commit checks..."

# Check Python code formatting
if command -v black &> /dev/null; then
    black --check services/
fi

# Check for common issues
if command -v flake8 &> /dev/null; then
    flake8 services/
fi

echo "Pre-commit checks completed"
EOF
        
        chmod +x .git/hooks/pre-commit
        print_status "Git hooks set up successfully"
    else
        print_warning "Git not available or not in a git repository"
    fi
}

# Main setup function
main() {
    print_status "Starting Aivta setup..."
    
    check_docker
    create_directories
    setup_env
    create_sample_config
    build_images
    init_database
    setup_git_hooks
    
    print_status "Setup completed successfully! 🎉"
    echo
    echo "Next steps:"
    echo "1. Review and update the .env file with your configuration"
    echo "2. Add your OpenAI API key to the .env file (if using OpenAI)"
    echo "3. Run 'docker-compose up' to start all services"
    echo "4. Visit http://localhost:8000/docs to see the AI Agent API"
    echo "5. Visit http://localhost:8080/docs to see the Text Game API"
    echo
    echo "For more information, see the README.md file"
}

# Run the main function
main "$@"