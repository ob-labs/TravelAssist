.PHONY: init clean start stop test help

# Default target
help:
	@echo "Available targets:"
	@echo "  make init  - Initialize the project (install dependencies, setup environment)"
	@echo "  make clean - Clean up generated files and caches"
	@echo "  make start - Start the travel assist application"
	@echo "  make stop  - Stop all running processes"
	@echo "  make test  - Run tests with pytest"

# Initialize the project
init:
	@echo "Initializing project..."
	@bash scripts/init.sh

# Clean up generated files
clean:
	@echo "Cleaning up..."
	@bash scripts/clean.sh

# Start the application
start:
	@echo "Starting travel assist application..."
	@bash scripts/start.sh

# Stop all processes
stop:
	@echo "Stopping all processes..."
	@bash scripts/stop.sh

# Run tests
test:
	@echo "Running tests..."
	@bash scripts/test.sh
