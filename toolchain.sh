#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

# Print colored messages
function print_step() {
    echo -e "\n\033[1;34m==>\033[0m \033[1m$1\033[0m"
}

function print_success() {
    echo -e "\033[1;32m==>\033[0m \033[1m$1\033[0m"
}

function print_error() {
    echo -e "\033[1;31m==>\033[0m \033[1m$1\033[0m"
}

function print_usage() {
    echo "Usage: ./toolchain.sh [OPTION]"
    echo "Set up the development environment for the Rust-Python JSON flattener."
    echo ""
    echo "Options:"
    echo "  --local       Set up local development environment"
    echo "  --docker      Build and enter a Docker container (default)"
    echo "  --help        Display this help message"
}

# Process command-line arguments
MODE="docker"
if [ "$#" -gt 0 ]; then
    case "$1" in
        --local)
            MODE="local"
            ;;
        --docker)
            MODE="docker"
            ;;
        --help)
            print_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            print_usage
            exit 1
            ;;
    esac
fi

# Function to create Docker entrypoint script
function create_entrypoint_script() {
    print_step "Creating Docker entrypoint script..."
    cat > docker-entrypoint.sh << 'EOF'
#!/bin/bash
set -e

# Activate virtual environment
source /app/venv/bin/activate

# Print welcome message
echo -e "\033[1;32m==>\033[0m \033[1mJSON Flattener Development Environment\033[0m"
echo -e "\033[1;32m==>\033[0m \033[1mRust is built and Python environment is ready!\033[0m"
echo ""
echo "Available commands:"
echo "  python python/data_generator.py           # Generate sample JSON files"
echo "  python python/benchmark.py data/*.json    # Run benchmarks"
echo ""

# Execute the command passed to docker run
exec "$@"
EOF
    chmod +x docker-entrypoint.sh
}

# Function to create Dockerfile
function create_dockerfile() {
    print_step "Creating Dockerfile..."
    cat > Dockerfile << EOF
FROM rust:slim-bullseye

# Install Python and dependencies
RUN apt-get update && apt-get install -y \\
    python3 \\
    python3-pip \\
    python3-venv \\
    pkg-config \\
    libssl-dev \\
    curl \\
    git \\
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Create and activate virtual environment
RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:\$PATH"
ENV VIRTUAL_ENV="/app/venv"

# Install Python dependencies
RUN pip install --upgrade pip && \\
    pip install pandas polars maturin pytest memory-profiler matplotlib tqdm faker

# Copy Rust project files
COPY Cargo.toml .
COPY src/ ./src/

# Copy Python files
COPY python/ ./python/

# Build the Rust library
RUN maturin develop --release

# Add an entrypoint script that activates the virtual environment
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Set up the entrypoint
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["bash"]
EOF
}

# Function to set up local environment
function setup_local() {
    print_step "Setting up local development environment..."
    
    # Check for required tools
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 not found. Please install Python 3.8 or later."
        exit 1
    fi
    
    if ! command -v rustc &> /dev/null; then
        print_error "Rust not found. Please install Rust using 'curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh'"
        exit 1
    fi
    
    # Create virtual environment
    print_step "Creating Python virtual environment..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    
    # Install Python dependencies
    print_step "Installing Python dependencies..."
    
    pip install --upgrade pip
    pip install pandas polars maturin pytest memory-profiler matplotlib tqdm faker
    
    # Build Rust library
    print_step "Building Rust library with maturin..."
    
    maturin develop --release
    
    print_success "Local environment setup completed successfully!"
    print_success "Rust library built and installed in virtual environment."
    echo ""
    echo "The virtual environment is now activated."
    echo "To activate it again in the future, run:"
    echo "  source venv/bin/activate"
    echo ""
    echo "To run the scripts:"
    echo "  python python/data_generator.py"
    echo "  python python/benchmark.py data/small_sample.json"
}

# Function to set up Docker environment
function setup_docker() {
    print_step "Setting up Docker development environment..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker not found. Please install Docker to use this option."
        exit 1
    fi
    
    # Create Docker entrypoint script
    create_entrypoint_script
    
    # Create Dockerfile
    create_dockerfile
    
    # Build Docker image
    print_step "Building Docker image..."
    docker build -t json-flattener-dev .
    
    # Run Docker container with current directory mounted
    print_step "Starting Docker container..."
    print_success "Docker environment ready! Your code is now running in the container."
    print_success "Any changes to the code in the mounted directory will be reflected in the container."
    
    # Mount the current directory to /app in the container
    docker run -it --rm -v "$(pwd):/app" json-flattener-dev
}

# Main execution based on mode
case "$MODE" in
    local)
        setup_local
        ;;
    docker)
        setup_docker
        ;;
esac
