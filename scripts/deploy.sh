#!/bin/bash

# Aivta Deployment Script
# This script handles deployment of the Aivta project

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_header() {
    echo -e "${BLUE}[DEPLOY]${NC} $1"
}

# Default values
ENVIRONMENT="development"
BUILD_FRESH=false
RUN_TESTS=true
BACKUP_DATA=true
SKIP_CONFIRMATION=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --environment|-e)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --build-fresh)
            BUILD_FRESH=true
            shift
            ;;
        --skip-tests)
            RUN_TESTS=false
            shift
            ;;
        --skip-backup)
            BACKUP_DATA=false
            shift
            ;;
        --yes|-y)
            SKIP_CONFIRMATION=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --environment, -e    Deployment environment (development, staging, production)"
            echo "  --build-fresh        Build Docker images from scratch"
            echo "  --skip-tests         Skip running tests before deployment"
            echo "  --skip-backup        Skip data backup before deployment"
            echo "  --yes, -y            Skip confirmation prompts"
            echo "  --help, -h           Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate environment
validate_environment() {
    case $ENVIRONMENT in
        development|staging|production)
            print_status "Deploying to $ENVIRONMENT environment"
            ;;
        *)
            print_error "Invalid environment: $ENVIRONMENT"
            print_error "Valid environments: development, staging, production"
            exit 1
            ;;
    esac
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if environment file exists
    if [ ! -f .env ]; then
        print_error ".env file not found"
        exit 1
    fi
    
    print_status "Prerequisites check passed"
}

# Backup data
backup_data() {
    if [ "$BACKUP_DATA" = true ]; then
        print_header "Backing up data..."
        
        # Create backup directory
        BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$BACKUP_DIR"
        
        # Backup database
        if docker-compose ps database | grep -q "Up"; then
            print_status "Backing up database..."
            docker-compose exec database pg_dump -U aivta_user aivta > "$BACKUP_DIR/database.sql"
        fi
        
        # Backup game saves
        if [ -d "services/text-game/saves" ]; then
            print_status "Backing up game saves..."
            cp -r services/text-game/saves "$BACKUP_DIR/"
        fi
        
        # Backup logs
        if [ -d "logs" ]; then
            print_status "Backing up logs..."
            cp -r logs "$BACKUP_DIR/"
        fi
        
        print_status "Backup completed: $BACKUP_DIR"
    else
        print_warning "Skipping data backup"
    fi
}

# Run tests
run_tests() {
    if [ "$RUN_TESTS" = true ]; then
        print_header "Running tests..."
        
        if [ -f "scripts/test.sh" ]; then
            bash scripts/test.sh --unit-only
        else
            print_warning "Test script not found, skipping tests"
        fi
    else
        print_warning "Skipping tests"
    fi
}

# Build Docker images
build_images() {
    print_header "Building Docker images..."
    
    if [ "$BUILD_FRESH" = true ]; then
        print_status "Building fresh images..."
        docker-compose build --no-cache
    else
        print_status "Building images..."
        docker-compose build
    fi
    
    print_status "Images built successfully"
}

# Deploy application
deploy_application() {
    print_header "Deploying application..."
    
    # Stop existing services
    print_status "Stopping existing services..."
    docker-compose down
    
    # Start services
    print_status "Starting services..."
    if [ "$ENVIRONMENT" = "production" ]; then
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
    else
        docker-compose up -d
    fi
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 30
    
    # Check service health
    check_service_health
    
    print_status "Application deployed successfully"
}

# Check service health
check_service_health() {
    print_status "Checking service health..."
    
    # Check AI Agent
    if curl -f http://localhost:8000/health &> /dev/null; then
        print_status "AI Agent service is healthy ✅"
    else
        print_error "AI Agent service is not healthy ❌"
        return 1
    fi
    
    # Check Text Game
    if curl -f http://localhost:8080/health &> /dev/null; then
        print_status "Text Game service is healthy ✅"
    else
        print_error "Text Game service is not healthy ❌"
        return 1
    fi
    
    # Check Database
    if docker-compose exec database pg_isready -U aivta_user -d aivta &> /dev/null; then
        print_status "Database service is healthy ✅"
    else
        print_error "Database service is not healthy ❌"
        return 1
    fi
    
    print_status "All services are healthy"
}

# Post-deployment tasks
post_deployment() {
    print_header "Running post-deployment tasks..."
    
    # Run database migrations (if any)
    print_status "Running database migrations..."
    # Add migration commands here if needed
    
    # Clear caches
    print_status "Clearing caches..."
    # Add cache clearing commands here if needed
    
    # Send deployment notification
    send_deployment_notification
    
    print_status "Post-deployment tasks completed"
}

# Send deployment notification
send_deployment_notification() {
    print_status "Sending deployment notification..."
    
    # Log deployment
    echo "$(date): Deployed to $ENVIRONMENT environment" >> logs/deployment.log
    
    # Add webhook notifications here if needed
    # curl -X POST -H 'Content-type: application/json' \
    #   --data '{"text":"Aivta deployed to '$ENVIRONMENT' environment"}' \
    #   YOUR_WEBHOOK_URL
    
    print_status "Deployment notification sent"
}

# Rollback function
rollback() {
    print_header "Rolling back deployment..."
    
    # Get the latest backup
    LATEST_BACKUP=$(ls -t backups/ | head -n 1)
    
    if [ -z "$LATEST_BACKUP" ]; then
        print_error "No backup found for rollback"
        return 1
    fi
    
    print_status "Rolling back to backup: $LATEST_BACKUP"
    
    # Stop services
    docker-compose down
    
    # Restore database
    if [ -f "backups/$LATEST_BACKUP/database.sql" ]; then
        print_status "Restoring database..."
        docker-compose up -d database
        sleep 10
        docker-compose exec -T database psql -U aivta_user -d aivta < "backups/$LATEST_BACKUP/database.sql"
    fi
    
    # Restore game saves
    if [ -d "backups/$LATEST_BACKUP/saves" ]; then
        print_status "Restoring game saves..."
        rm -rf services/text-game/saves
        cp -r "backups/$LATEST_BACKUP/saves" services/text-game/
    fi
    
    # Start services
    docker-compose up -d
    
    print_status "Rollback completed"
}

# Confirmation prompt
confirm_deployment() {
    if [ "$SKIP_CONFIRMATION" = false ]; then
        echo
        print_warning "You are about to deploy to the $ENVIRONMENT environment."
        echo "This will:"
        echo "- Stop and restart all services"
        echo "- Apply any new configuration changes"
        echo "- Potentially cause brief downtime"
        echo
        read -p "Are you sure you want to continue? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status "Deployment cancelled"
            exit 0
        fi
    fi
}

# Main deployment function
main() {
    print_header "Starting Aivta Deployment"
    
    validate_environment
    check_prerequisites
    confirm_deployment
    
    backup_data
    run_tests
    build_images
    deploy_application
    post_deployment
    
    print_status "Deployment completed successfully! 🎉"
    echo
    echo "Services are now running:"
    echo "- AI Agent API: http://localhost:8000"
    echo "- Text Game API: http://localhost:8080"
    echo "- API Documentation: http://localhost:8000/docs"
    echo
    echo "To view logs: docker-compose logs -f"
    echo "To stop services: docker-compose down"
    echo "To rollback: $0 --rollback"
}

# Handle rollback command
if [ "$1" = "--rollback" ]; then
    rollback
    exit 0
fi

# Run the main function
main "$@"