# dzai

An attempt at an agent that does Python like I do!

## Installation

```bash
uv sync
```

## Usage

```bash
uv run dzai api-research-agent -q "Query"

# Example
uv run dzai api-research-agent -q "How do I show thinking in logs when using pydantic AI - https://github.com/pydantic/pydantic-ai"
```

## Agents

Agents are defined via YAML files located in `src/dzai/agents`.
Adding agents is as simple as adding a new YAML file in the folder, but please add the agent name to the help string in `cli.py`.

## prek

This is a Rust based pre-commit.

### Usage

```bash
# Install
uv add --group dev prek

# Install the hook
uv run prek install

# Run the hook, although this should be automatic after installing prek
uv run prek run
```
