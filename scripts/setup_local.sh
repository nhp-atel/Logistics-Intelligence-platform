#!/bin/bash
# Local development setup script

set -e

echo "=== Logistics Data Platform - Local Setup ==="
echo

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is required but not installed."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is required but not installed."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "ERROR: Docker Compose is required but not installed."
    exit 1
fi

echo "✓ All prerequisites met"
echo

# Create virtual environment
echo "Creating Python virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate and install dependencies
echo "Installing Python dependencies..."
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
echo "✓ Dependencies installed"
echo

# Copy environment file
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created (please edit with your settings)"
else
    echo "✓ .env file already exists"
fi

# Create required directories
echo "Creating required directories..."
mkdir -p data/generated
mkdir -p credentials
mkdir -p airflow/logs
echo "✓ Directories created"
echo

# Install pre-commit hooks
echo "Setting up pre-commit hooks..."
pre-commit install
echo "✓ Pre-commit hooks installed"
echo

# Start Docker services
echo "Starting Docker services..."
docker-compose up -d
echo "Waiting for services to be healthy..."
sleep 15

# Check service health
echo "Checking service health..."
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo "✓ Airflow is running at http://localhost:8080"
else
    echo "⚠ Airflow may still be starting up"
fi

if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ API is running at http://localhost:8000"
else
    echo "⚠ API may still be starting up"
fi

echo
echo "=== Setup Complete ==="
echo
echo "Next steps:"
echo "  1. Edit .env file with your settings"
echo "  2. Generate sample data: make generate-data"
echo "  3. Access Airflow: http://localhost:8080 (airflow/airflow)"
echo "  4. Access API docs: http://localhost:8000/docs"
echo "  5. Access Jupyter: http://localhost:8888"
echo
