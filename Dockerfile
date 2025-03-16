FROM rust:slim-bullseye

# Install Python and dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    pkg-config \
    libssl-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Create and activate virtual environment
RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"
ENV VIRTUAL_ENV="/app/venv"

# Install Python dependencies
RUN pip install --upgrade pip && \
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
