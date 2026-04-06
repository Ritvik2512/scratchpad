#!/bin/bash

# Quick setup script for MCP Memory with standalone Qdrant

set -e

echo "🚀 Setting up MCP Memory Server with Qdrant..."

# Stop any existing Qdrant containers
echo "🧹 Cleaning up existing containers..."
docker stop qdrant-test 2>/dev/null || true
docker rm qdrant-test 2>/dev/null || true

# Start Qdrant container
echo "🐳 Starting Qdrant container..."
docker run -d -p 6333:6333 -p 6334:6334 --name qdrant-test qdrant/qdrant:latest

# Wait for Qdrant to be ready
echo "⏳ Waiting for Qdrant to start..."
sleep 5

# Activate virtual environment and install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Test the MCP server
echo "🧪 Testing MCP server..."
timeout 10s python memory.py --agent-id test-agent --host localhost --port 6333 2>/dev/null || true

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Add config to Claude:"
echo "   check claude_desktop_config.json"
echo ""
echo "2. Restart Claude Desktop"
echo ""
echo "🔧 Useful commands:"
echo "   View Qdrant logs: docker logs qdrant-test"
echo "   Stop Qdrant: docker stop qdrant-test"
echo "   Test server: python memory.py --agent-id test --host localhost --port 6333"
echo ""
echo "🌐 Qdrant Dashboard: http://localhost:6333/dashboard"
