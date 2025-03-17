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

# Function to create Poetry configuration file if it doesn't exist
function create_poetry_config() {
    if [ ! -f "pyproject.toml" ]; then
        print_step "Creating Poetry configuration (pyproject.toml)..."
        cat > pyproject.toml << EOF
[build-system]
requires = ["maturin>=1.0,<2.0"]
build-backend = "maturin"

[tool.poetry]
name = "json-flattener"
version = "0.1.0"
description = "High-performance JSON flattener with Rust backend"
authors = ["Paul Nikholas Lopez <nik.lopez381@gmail.com.com>"]
readme = "README.md"
packages = [{include = "python"}]

[tool.poetry.dependencies]
python = "^3.8"
pandas = "^2.0.0"
polars = {version = "^0.19.0", optional = true}

[tool.poetry.group.dev.dependencies]
pytest = "^7.0.0"
memory-profiler = "^0.61.0"
matplotlib = "^3.6.0"
tqdm = "^4.64.0"
faker = "^13.0.0"

[tool.poetry.extras]
polaris = ["polars"]

[tool.maturin]
module-name = "json_flattener_rust"
python-source = "python"
features = ["pyo3/extension-module"]
EOF
        print_success "Poetry configuration created."
    else
        print_step "Using existing pyproject.toml configuration."
    fi
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
    pip install pandas polars maturin pytest memory-profiler matplotlib tqdm faker pyarrow
    
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
    
    # Create Docker entrypoint script with simplified approach
    print_step "Creating Docker entrypoint script..."
    cat > docker-entrypoint.sh << 'EOF'
#!/bin/bash
set -e

# Install Python dependencies directly
pip install --no-cache-dir pandas polars pytest memory-profiler matplotlib tqdm faker pyarrow

# Build Rust library
cd /app
cargo build --release
maturin develop --release

echo "==> Environment is ready!"
echo "Available commands:"
echo "  python python/data_generator.py"
echo "  python python/benchmark.py data/small_sample.json"

# Execute the command
exec "$@"
EOF
    chmod +x docker-entrypoint.sh
    
    # Create simplified Dockerfile
    print_step "Creating Dockerfile..."
    cat > Dockerfile << EOF
FROM rust:slim-bullseye

# Install Python and required system dependencies
RUN apt-get update && apt-get install -y \\
    python3 \\
    python3-pip \\
    python3-dev \\
    pkg-config \\
    libssl-dev \\
    && rm -rf /var/lib/apt/lists/*

# Ensure Python and pip are available without version suffix
RUN which python3 || true && which pip3 || true && \\
    which python || true && which pip || true && \\
    if [ ! -e /usr/bin/python ]; then ln -s \$(which python3) /usr/local/bin/python || true; fi && \\
    if [ ! -e /usr/bin/pip ]; then ln -s \$(which pip3) /usr/local/bin/pip || true; fi

# Install maturin
RUN pip install maturin

# Set working directory
WORKDIR /app

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["bash"]
EOF
    
    # Create data directory if it doesn't exist
    mkdir -p data
    
    # Build Docker image
    print_step "Building Docker image..."
    docker build -t json-flattener-dev .
    
    # Run Docker container with current directory mounted
    print_step "Starting Docker container..."
    print_success "Docker environment ready!"
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
