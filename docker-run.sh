#!/bin/bash

# Docker deployment script for Genshin Impact Personal Assistant API
# Usage: ./docker-run.sh [dev|prod|tools|stop|clean]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if .env file exists
check_env_file() {
    if [ ! -f .env ]; then
        print_error ".env file not found!"
        print_status "Please create a .env file with your API keys."
        print_status "Required environment variables:"
        print_status "  - MONGODB_PASSWORD"
        print_status "  - GOOGLE_API_KEY"
        print_status "  - GOOGLE_CSE_ID"
        print_status "  - GOOGLE_CSE_API_KEY"
        exit 1
    fi
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Function to create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    mkdir -p logs
    mkdir -p docker/nginx/ssl
    print_success "Directories created"
}

# Development environment
run_dev() {
    print_status "Starting development environment..."
    check_env_file
    check_docker
    create_directories
    
    print_status "Building and starting development containers..."
    docker-compose -f docker-compose.dev.yml up --build -d
    
    print_success "Development environment started!"
    echo ""
    echo "🚀 Services available at:"
    echo "   📖 API Documentation: http://localhost:8000/docs"
    echo "   ❤️  Health Check: http://localhost:8000/health"
    echo "   🔴 Redis Commander: http://localhost:8082"
    echo "   🗄️  MongoDB Atlas: Use web interface at https://cloud.mongodb.com"
    echo ""
    echo "📋 To view logs: docker-compose -f docker-compose.dev.yml logs -f"
    echo "🛑 To stop: ./docker-run.sh stop"
}

# Production environment
run_prod() {
    print_status "Starting production environment..."
    check_env_file
    check_docker
    create_directories
    
    print_status "Building and starting production containers..."
    docker-compose up --build -d
    
    print_success "Production environment started!"
    echo ""
    echo "🚀 Services available at:"
    echo "   📖 API Documentation: http://localhost:8000/docs"
    echo "   ❤️  Health Check: http://localhost:8000/health"
    echo ""
    echo "📋 To view logs: docker-compose logs -f"
    echo "🛑 To stop: ./docker-run.sh stop"
}

# Production with Nginx
run_prod_nginx() {
    print_status "Starting production environment with Nginx..."
    check_env_file
    check_docker
    create_directories
    
    print_status "Building and starting production containers with Nginx..."
    docker-compose --profile production up --build -d
    
    print_success "Production environment with Nginx started!"
    echo ""
    echo "🚀 Services available at:"
    echo "   🌐 API (via Nginx): http://localhost"
    echo "   📖 API Documentation: http://localhost/docs"
    echo "   ❤️  Health Check: http://localhost/health"
    echo ""
    echo "📋 To view logs: docker-compose logs -f"
    echo "🛑 To stop: ./docker-run.sh stop"
}

# Tools environment (MongoDB Express, etc.)
run_tools() {
    print_status "Starting tools environment..."
    check_env_file
    check_docker
    create_directories
    
    print_status "Starting tools..."
    docker-compose --profile tools up -d redis
    
    print_success "Tools environment started!"
    echo ""
    echo "🛠️  Tools available at:"
    echo "   🗄️  MongoDB Atlas: https://cloud.mongodb.com"
    echo "   🔴 Redis: localhost:6379"
    echo ""
    echo "🛑 To stop: ./docker-run.sh stop"
}

# Stop all containers
stop_containers() {
    print_status "Stopping all containers..."
    
    # Stop development containers
    if [ -f docker-compose.dev.yml ]; then
        docker-compose -f docker-compose.dev.yml down
    fi
    
    # Stop production containers
    if [ -f docker-compose.yml ]; then
        docker-compose down
        docker-compose --profile production down
        docker-compose --profile tools down
    fi
    
    print_success "All containers stopped"
}

# Clean up everything
clean_all() {
    print_warning "This will remove all containers, volumes, and images. Are you sure? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_status "Cleaning up everything..."
        
        # Stop containers
        stop_containers
        
        # Remove volumes
        docker volume rm $(docker volume ls -q | grep genshin) 2>/dev/null || true
        
        # Remove images
        docker rmi $(docker images | grep genshin | awk '{print $3}') 2>/dev/null || true
        
        # Clean up Docker system
        docker system prune -f
        
        print_success "Cleanup completed"
    else
        print_status "Cleanup cancelled"
    fi
}

# Show logs
show_logs() {
    if [ -f docker-compose.dev.yml ] && [ "$(docker-compose -f docker-compose.dev.yml ps -q)" ]; then
        docker-compose -f docker-compose.dev.yml logs -f
    elif [ -f docker-compose.yml ] && [ "$(docker-compose ps -q)" ]; then
        docker-compose logs -f
    else
        print_error "No running containers found"
    fi
}

# Show status
show_status() {
    print_status "Container status:"
    docker ps --filter "name=genshin" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
}

# Main script logic
case "${1:-}" in
    "dev")
        run_dev
        ;;
    "prod")
        run_prod
        ;;
    "prod-nginx")
        run_prod_nginx
        ;;
    "tools")
        run_tools
        ;;
    "stop")
        stop_containers
        ;;
    "clean")
        clean_all
        ;;
    "logs")
        show_logs
        ;;
    "status")
        show_status
        ;;
    *)
        echo "🐋 Genshin Impact Personal Assistant API - Docker Deployment"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  dev         Start development environment with hot reload"
        echo "  prod        Start production environment"
        echo "  prod-nginx  Start production environment with Nginx"
        echo "  tools       Start only database and management tools"
        echo "  stop        Stop all containers"
        echo "  clean       Remove all containers, volumes, and images"
        echo "  logs        Show container logs"
        echo "  status      Show container status"
        echo ""
        echo "Examples:"
        echo "  $0 dev      # Start development environment"
        echo "  $0 prod     # Start production environment"
        echo "  $0 stop     # Stop all containers"
        echo ""
        exit 1
        ;;
esac 