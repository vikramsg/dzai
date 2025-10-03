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

## Logging

The default log level is set to `INFO`. To run an agent with `DEBUG` level, either set `LOG_LEVEL=debug` in `.env` or prepend when running

```sh
LOG_LEVEL=debug uv run dzai ...
```

## Anthropic

### Extended Thinking

To enable extended thinking for Anthropic models, add the `anthropic_thinking` configuration to your agent's YAML file:

```yaml
model_settings:
  anthropic_thinking:
    type: "enabled"
    budget_tokens: 16000
```

**Configuration:**
- `budget_tokens`: Minimum 1,024 tokens (recommended: 16,000+ for complex tasks, up to 128,000)
- Compatible models: Claude Opus 4.1, Opus 4, Sonnet 4.5, Sonnet 4, Sonnet 3.7

**Important limitations:**
- Cannot use thinking with structured output (`BaseModel` as `output_type`)
- Use `PromptedOutput` instead if you need structured output with thinking

Thinking logs will be captured and displayed via the existing `ThinkingPartDelta` handler in the agent streaming logic.

## Gemini

Lots of workaround are required to make Gemini work.

1. The default retring client that works for Anthropic and OpenAI does not work for Gemini since Pydantic has its own custom implementation for Gemini.

    - So we need a special retrying client for Gemini.
    - We need `LOG_LEVEL` to be used via `env` since we have to modify the retrying client to get the bare minimum log messages.

2. Gemini does not allow combining a tool and search. So we have created a separate agent, that only does search. We need to refine this to provide pure search results.
