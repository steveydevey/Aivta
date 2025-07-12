#!/bin/bash

# Aivta Test Runner Script
# This script runs the full test suite for the Aivta project

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
    echo -e "${BLUE}[TEST]${NC} $1"
}

# Default values
RUN_UNIT=true
RUN_INTEGRATION=true
RUN_COVERAGE=false
VERBOSE=false
STOP_ON_FAILURE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --unit-only)
            RUN_INTEGRATION=false
            shift
            ;;
        --integration-only)
            RUN_UNIT=false
            shift
            ;;
        --coverage)
            RUN_COVERAGE=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --stop-on-failure|-x)
            STOP_ON_FAILURE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --unit-only          Run only unit tests"
            echo "  --integration-only   Run only integration tests"
            echo "  --coverage           Run tests with coverage report"
            echo "  --verbose, -v        Verbose output"
            echo "  --stop-on-failure, -x Stop on first failure"
            echo "  --help, -h           Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Set pytest options
PYTEST_OPTS=""
if [ "$VERBOSE" = true ]; then
    PYTEST_OPTS="$PYTEST_OPTS -v"
fi

if [ "$STOP_ON_FAILURE" = true ]; then
    PYTEST_OPTS="$PYTEST_OPTS -x"
fi

if [ "$RUN_COVERAGE" = true ]; then
    PYTEST_OPTS="$PYTEST_OPTS --cov=services --cov-report=html --cov-report=term-missing"
fi

# Function to install test dependencies
install_dependencies() {
    print_status "Installing test dependencies..."
    
    if [ -f tests/requirements.txt ]; then
        pip install -r tests/requirements.txt
    else
        print_warning "tests/requirements.txt not found, installing basic dependencies"
        pip install pytest pytest-asyncio pytest-cov httpx
    fi
    
    print_status "Dependencies installed"
}

# Function to check if services are running
check_services() {
    print_status "Checking if services are running..."
    
    # Check if Docker Compose services are running
    if docker-compose ps | grep -q "Up"; then
        print_status "Services are running"
        return 0
    else
        print_warning "Services are not running. Starting them..."
        docker-compose up -d
        sleep 10
        return 1
    fi
}

# Function to run unit tests
run_unit_tests() {
    print_header "Running Unit Tests"
    
    if [ "$RUN_UNIT" = true ]; then
        python -m pytest tests/ -m "unit or not integration" $PYTEST_OPTS
        local exit_code=$?
        
        if [ $exit_code -eq 0 ]; then
            print_status "Unit tests passed ✅"
        else
            print_error "Unit tests failed ❌"
            return $exit_code
        fi
    else
        print_status "Skipping unit tests"
    fi
}

# Function to run integration tests
run_integration_tests() {
    print_header "Running Integration Tests"
    
    if [ "$RUN_INTEGRATION" = true ]; then
        # Ensure services are running for integration tests
        check_services
        
        python -m pytest tests/ -m "integration" $PYTEST_OPTS
        local exit_code=$?
        
        if [ $exit_code -eq 0 ]; then
            print_status "Integration tests passed ✅"
        else
            print_error "Integration tests failed ❌"
            return $exit_code
        fi
    else
        print_status "Skipping integration tests"
    fi
}

# Function to run service-specific tests
run_service_tests() {
    print_header "Running Service-Specific Tests"
    
    # Test AI Agent service
    if [ -f "tests/test_ai_agent.py" ]; then
        print_status "Testing AI Agent service..."
        python -m pytest tests/test_ai_agent.py $PYTEST_OPTS
    fi
    
    # Test Text Game service
    if [ -f "tests/test_text_game.py" ]; then
        print_status "Testing Text Game service..."
        python -m pytest tests/test_text_game.py $PYTEST_OPTS
    fi
}

# Function to run Docker-based tests
run_docker_tests() {
    print_header "Running Docker-based Tests"
    
    # Test that services can be built
    print_status "Testing Docker builds..."
    docker-compose build --no-cache
    
    # Test that services can start
    print_status "Testing service startup..."
    docker-compose up -d
    sleep 10
    
    # Test health checks
    print_status "Testing service health..."
    curl -f http://localhost:8000/health || {
        print_error "AI Agent health check failed"
        return 1
    }
    
    curl -f http://localhost:8080/health || {
        print_error "Text Game health check failed"
        return 1
    }
    
    print_status "Docker tests passed ✅"
}

# Function to generate coverage report
generate_coverage_report() {
    if [ "$RUN_COVERAGE" = true ]; then
        print_header "Generating Coverage Report"
        
        if [ -f ".coverage" ]; then
            print_status "Coverage report generated in htmlcov/"
            print_status "Open htmlcov/index.html in your browser to view the report"
        else
            print_warning "No coverage data found"
        fi
    fi
}

# Function to clean up test artifacts
cleanup() {
    print_status "Cleaning up test artifacts..."
    
    # Remove test database files
    rm -f test_*.db
    
    # Remove pytest cache
    rm -rf .pytest_cache
    
    # Remove coverage files if not requested
    if [ "$RUN_COVERAGE" = false ]; then
        rm -f .coverage
        rm -rf htmlcov
    fi
    
    print_status "Cleanup completed"
}

# Main test function
main() {
    print_header "Starting Aivta Test Suite"
    
    # Install dependencies
    install_dependencies
    
    # Run tests
    local exit_code=0
    
    if [ "$RUN_UNIT" = true ]; then
        run_unit_tests || exit_code=$?
    fi
    
    if [ "$RUN_INTEGRATION" = true ]; then
        run_integration_tests || exit_code=$?
    fi
    
    # Run service-specific tests
    run_service_tests || exit_code=$?
    
    # Run Docker tests
    run_docker_tests || exit_code=$?
    
    # Generate coverage report
    generate_coverage_report
    
    # Cleanup
    cleanup
    
    if [ $exit_code -eq 0 ]; then
        print_status "All tests passed! 🎉"
    else
        print_error "Some tests failed. Check the output above for details."
    fi
    
    exit $exit_code
}

# Run the main function
main "$@"