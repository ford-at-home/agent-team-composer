FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy AWS requirements and install Python dependencies
COPY aws/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the main github-backlog-generator source code
COPY github-backlog-generator/ ./github-backlog-generator/

# Change to the source directory and install the package
WORKDIR /app/github-backlog-generator
RUN pip install -e .

# Set back to app directory for execution
WORKDIR /app

# Default command using the proper entry point
CMD ["github-backlog-generator"]