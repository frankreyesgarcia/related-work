#!/bin/bash
# One-command setup for research-digest
set -e
cd "$(dirname "$0")"

echo "🔧 Setting up research-digest..."

# Check Python 3
if ! command -v python3 &>/dev/null; then
  echo "❌ Python 3 is required. Install it from https://python.org"
  exit 1
fi

# Check npm / Node
if ! command -v npm &>/dev/null; then
  echo "❌ Node.js/npm is required. Install it from https://nodejs.org"
  exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install feedparser requests pyyaml

# Install OpenCode CLI
echo "📦 Installing OpenCode CLI..."
npm install -g opencode-ai

# Create output directories
echo "📁 Creating output directories..."
mkdir -p summaries digests logs

# Copy .env template if not present
if [ ! -f .env ]; then
  cp .env.example .env
  echo "📋 Created .env from .env.example — edit it with your SMTP credentials"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit config.yaml — set your topic and email address"
echo "  2. Edit .env — set your SMTP credentials"
echo "  3. Authenticate with OpenCode Zen (free):"
echo "       opencode auth login"
echo "       → Select 'OpenCode Zen' → sign up at opencode.ai → paste your API key"
echo "  4. Test the pipeline:"
echo "       ./run.sh --dry-run"
echo ""
echo "To run daily via cron (8am local time):"
echo "  crontab -e"
echo "  0 8 * * * cd $(pwd) && ./run.sh >> logs/cron.log 2>&1"
