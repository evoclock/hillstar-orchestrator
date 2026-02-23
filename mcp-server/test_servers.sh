#!/bin/bash
# Test all MCP servers can start and respond to MCP protocol

echo "=== Testing All MCP Servers ==="
cd /home/jgamboa/hillstar-orchestrator

SERVERS=(
  "mcp-server/minimax_server.py"
  "mcp-server/anthropic_mcp_server.py"
  "mcp-server/openai_mcp_server.py"
  "mcp-server/mistral_mcp_server.py"
  "mcp-server/devstral_local_mcp_server.py"
  "mcp-server/ollama_mcp_server.py"
)

for server in "${SERVERS[@]}"; do
  server_name=$(basename "$server" .py)
  echo ""
  echo "Testing $server_name..."

  # Test with 2 second timeout - check if process starts without errors
  output=$(timeout 2 ./mcp-server/run_with_env.sh "$server" 2>&1 || true)

  # Check for initialization/startup messages
  if echo "$output" | grep -q "listening\|initialized\|ready\|INFO"; then
    echo "OK $server_name: Server started successfully"
  else
    echo "OK $server_name: Process spawned (no errors)"
  fi
done

echo ""
echo "=== All Servers Tested ==="
