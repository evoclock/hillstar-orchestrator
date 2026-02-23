#!/bin/bash
# Load .env file from project root, then run the MCP server
# Usage: run_with_env.sh <path_to_server.py> [additional_args...]

set -a  # Export all variables
if [ -f "$(dirname "$0")/../.env" ]; then
    source "$(dirname "$0")/../.env"
fi
set +a

# Run the Python MCP server with all arguments
exec python3 "$@"
