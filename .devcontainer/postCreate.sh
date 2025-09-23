#!/bin/bash
# Test this postCreate command properly
set -ex

# Install neovim for some sane editing in the terminal
sudo apt update && sudo apt install -y neovim

# Download and install nvm:
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash

\. "/usr/local/share/nvm/nvm.sh"
# Download and install Node.js:
nvm install 22

# Make zsh load .env by default
echo -e 'ZSH_DOTENV_PROMPT=false\n'"$(cat ~/.zshrc 2>/dev/null || echo '')" > ~/.zshrc

echo "Installing CLI tools..."
npm install -g @openai/codex @anthropic-ai/claude-code

echo "Fixing workspace ownership..."
sudo chown -R vscode:vscode /workspaces

echo "postCreate script completed successfully!"
