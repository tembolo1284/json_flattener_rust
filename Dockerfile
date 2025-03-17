FROM rust:slim-bullseye

# Install Python and required system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Ensure Python and pip are available without version suffix
RUN which python3 || true && which pip3 || true && \
    which python || true && which pip || true && \
    if [ ! -e /usr/bin/python ]; then ln -s $(which python3) /usr/local/bin/python || true; fi && \
    if [ ! -e /usr/bin/pip ]; then ln -s $(which pip3) /usr/local/bin/pip || true; fi

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
