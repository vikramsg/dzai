.PHONY: help build rebuild up down clean logs shell

help:
	@echo "Available commands:"
	@echo "  make build     - Build the devcontainer"
	@echo "  make rebuild   - Rebuild the devcontainer from scratch (no cache)"
	@echo "  make up        - Start the devcontainer"
	@echo "  make down      - Stop the devcontainer"
	@echo "  make clean     - Remove devcontainer and volumes"
	@echo "  make logs      - Show devcontainer logs"
	@echo "  make shell     - Open a shell in the devcontainer"

build:
	@echo "Building devcontainer..."
	devcontainer build --workspace-folder .

rebuild:
	@echo "Rebuilding devcontainer from scratch (no cache)..."
	devcontainer build --workspace-folder . --no-cache

up:
	@echo "Starting devcontainer..."
	devcontainer up --workspace-folder .

down:
	@echo "Stopping devcontainer..."
	docker compose -f .devcontainer/docker-compose.yml down 2>/dev/null || \
	docker stop $$(docker ps -q --filter "label=devcontainer.local_folder=$$(pwd)") 2>/dev/null || \
	echo "No running devcontainer found"

clean:
	@echo "Cleaning up devcontainer and volumes..."
	docker compose -f .devcontainer/docker-compose.yml down -v 2>/dev/null || true
	docker rm -f $$(docker ps -aq --filter "label=devcontainer.local_folder=$$(pwd)") 2>/dev/null || true
	docker volume rm $$(docker volume ls -q --filter "label=devcontainer.local_folder=$$(pwd)") 2>/dev/null || true
	@echo "Cleanup complete"

logs:
	@echo "Showing devcontainer logs..."
	docker logs $$(docker ps -q --filter "label=devcontainer.local_folder=$$(pwd)") -f

shell:
	@echo "Opening shell in devcontainer..."
	devcontainer exec --workspace-folder . /bin/zsh
