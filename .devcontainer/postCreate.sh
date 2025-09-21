#!/bin/bash
set -ex

# Install pnpm
curl -fsSL https://get.pnpm.io/install.sh | sh -

# Make zsh load .env by default
echo 'export ZSH_DOTENV_PROMPT=false' >> ~/.zshrc

echo "Installing CLI tools..."
pnpm install -g @openai/codex @anthropic-ai/claude-code

echo "postCreate script completed successfully!"
