#!/bin/bash
# Test this postCreate command properly
set -ex

brew install tmux neovim

# Set up SSH keys for remote access
if [ -d "/home/vscode/.ssh_host" ]; then
    echo "Setting up SSH keys..."
    mkdir -p ~/.ssh
    cp -r /home/vscode/.ssh_host/* ~/.ssh/ 2>/dev/null || true
    chmod 700 ~/.ssh
    chmod 600 ~/.ssh/* 2>/dev/null || true
    chmod 644 ~/.ssh/*.pub 2>/dev/null || true

    # Add authorized keys for SSH access
    if [ -f ~/.ssh/id_rsa.pub ]; then
        cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
    fi
    if [ -f ~/.ssh/id_ed25519.pub ]; then
        cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys
    fi
    chmod 600 ~/.ssh/authorized_keys 2>/dev/null || true
    echo "SSH keys configured successfully!"
fi

# Download and install nvm:
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash

\. "/usr/local/share/nvm/nvm.sh"
# Download and install Node.js:
nvm install 22

# Make zsh load .env by default
echo -e 'ZSH_DOTENV_PROMPT=false\n'"$(cat ~/.zshrc 2>/dev/null || echo '')" > ~/.zshrc

# Set up tmux configuration from local machine
if [ -f "/home/vscode/.tmux_host/.tmux.conf" ]; then
    echo "Setting up tmux configuration from local machine..."
    cp /home/vscode/.tmux_host/.tmux.conf ~/.tmux.conf
    echo "Tmux configuration loaded!"
fi

# Install TPM (Tmux Plugin Manager)
echo "Installing TPM (Tmux Plugin Manager)..."
if [ ! -d ~/.tmux/plugins/tpm ]; then
    git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
    echo "TPM installed successfully!"
else
    echo "TPM already installed, skipping..."
fi

# Set up neovim configuration from local machine
if [ -d "/home/vscode/.config_host/nvim" ]; then
    echo "Setting up neovim configuration from local machine..."
    mkdir -p ~/.config/nvim
    cp -r /home/vscode/.config_host/nvim/* ~/.config/nvim/
    echo "Neovim configuration loaded!"
fi

echo "Installing CLI tools..."
npm install -g @openai/codex @anthropic-ai/claude-code

echo "postCreate script completed successfully!"
