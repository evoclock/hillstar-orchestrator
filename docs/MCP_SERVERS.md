# MCP Servers: Setup, Integration, and Security

This document describes Hillstar's Model Context Protocol (MCP) server implementations and how to set them up.

---

## Overview

MCP servers are subprocess-based provider implementations that handle:

- Model initialization and configuration
- Request/response JSON-RPC protocol
- Error detection and credential security
- Independent resource management
- Isolated execution environments

### Architecture Benefits

Isolation:

- Each provider runs in separate subprocess
- Failures don't crash orchestrator
- Resource limits per provider

Security:

- API keys never passed to untrusted code
- Subprocess can't access other credentials
- Error messages filtered before returning

Flexibility:

- Providers can be updated independently
- Custom providers can be implemented
- Easy to add new models or capabilities

---

## Implemented MCP Servers

### 1. Anthropic MCP Server

**Location:** mcp-server/anthropic_mcp_server.py

**Responsibility:** Handle Claude model invocations via subprocess

**Models Supported:**

- claude-opus-4-6
- claude-sonnet-4-5-20250929
- claude-haiku-4-5-20251001

**Implementation:**

- Spawns as: python mcp-server/anthropic_mcp_server.py
- Protocol: JSON-RPC 2.0 over stdin/stdout
- Lifecycle: Managed by models/anthropic_mcp_model.py

**API Key Handling:**

- Receives ANTHROPIC_API_KEY via environment
- Validates before initialization
- Never logs or returns the key

**Error Handling:**

- Detects auth failures early
- Returns helpful error messages
- Redacts sensitive info from errors

### 2. OpenAI MCP Server

**Location:** mcp-server/openai_mcp_server.py

**Responsibility:** Handle GPT model invocations

**Models Supported:**

- gpt-5.2-pro
- gpt-5.2
- gpt-5-mini
- o3, o3-mini
- Legacy: gpt-4o, gpt-4, gpt-3.5-turbo

**Implementation:**

- Spawns subprocess
- Uses OpenAI Python SDK
- Implements JSON-RPC protocol

**Configuration:**

- OPENAI_API_KEY environment variable
- Optional: OPENAI_ORG_ID for organization
- Optional: Base URL override

**Special Features:**

- Handles token usage tracking
- Supports vision capabilities
- Manages function calling

### 3. Mistral MCP Server

**Location:** mcp-server/mistral_mcp_server.py

**Responsibility:** Handle Mistral model invocations

**Models Supported:**

- mistral-large-3
- mistral-medium-3.1
- ministral-3b, ministral-8b
- codestral
- devstral-2

**Implementation:**

- Subprocess-based execution
- Mistral SDK integration
- JSON-RPC protocol

**Configuration:**

- MISTRAL_API_KEY environment variable
- Optional: Base URL configuration

### 4. Google AI Studio MCP Server

**Location:** mcp-server/google_ai_studio_mcp_server.py

**Responsibility:** Handle Gemini model invocations

**Models Supported:**

- gemini-3.1-pro-preview
- gemini-3-flash-preview
- gemini-2.5-pro
- gemini-2.5-flash
- gemini-2.5-flash-lite

**Implementation:**

- Google Generative AI SDK
- Free tier + paid API support
- JSON-RPC wrapper

**Configuration:**

- GOOGLE_API_KEY environment variable
- Free tier has rate limits
- Paid tier has higher quotas

### 5. Ollama MCP Server

**Location:** mcp-server/ollama_mcp_server.py

**Responsibility:** Handle local Ollama model invocations

**Models Supported:**

- devstral-2:123b-cloud
- minimax-m2.1:cloud
- glm-4.7:cloud
- Custom models (via Ollama)

**Implementation:**

- Communicates with local Ollama instance
- HTTP client to Ollama API
- No authentication required

**Configuration:**

- OLLAMA_BASE_URL (default: <http://localhost:11434>)
- Requires Ollama to be running
- Models must be pre-pulled

**Usage:**

```bash
# Start Ollama
ollama serve

# Pull model
ollama pull devstral-2

# Hillstar will auto-detect and use
```

### 6. Devstral Local MCP Server

**Location:** mcp-server/devstral_local_mcp_server.py

**Responsibility:** Handle local Devstral inference

**Model Supported:**

- devstral-small-2-24b

**Implementation:**

- Subprocess wrapper around local inference
- Configurable inference engine
- Resource management

**Configuration:**

- MODEL_PATH: Path to model weights
- DEVICE: cuda / cpu
- QUANTIZATION: Optional quantization settings

---

## MCP Protocol Details

### JSON-RPC 2.0 Protocol

All servers implement JSON-RPC 2.0 for communication.

#### Initialize Request

```json
{
 "jsonrpc": "2.0",
 "id": 1,
 "method": "initialize",
 "params": {
 "provider": "anthropic",
 "config": {}
 }
}
```

Note: API keys are passed via environment variables (e.g., ANTHROPIC_API_KEY), never in JSON-RPC params.

#### Initialize Response

```json
{
 "jsonrpc": "2.0",
 "id": 1,
 "result": {
 "provider": "anthropic",
 "models": ["claude-opus-4-6", "claude-sonnet-4-5"],
 "status": "ready"
 }
}
```

#### Model Call Request

```json
{
 "jsonrpc": "2.0",
 "id": 2,
 "method": "call",
 "params": {
 "model": "claude-opus-4-6",
 "messages": [
 {
 "role": "user",
 "content": "Hello"
 }
 ],
 "temperature": 0.7,
 "max_tokens": 1000
 }
}
```

#### Model Call Response

```json
{
 "jsonrpc": "2.0",
 "id": 2,
 "result": {
 "content": "Hello! How can I help?",
 "stop_reason": "end_turn",
 "input_tokens": 10,
 "output_tokens": 5,
 "cost_usd": 0.15
 }
}
```

#### Error Response

```json
{
 "jsonrpc": "2.0",
 "id": 2,
 "error": {
 "code": -32603,
 "message": "API Error",
 "data": {
 "error_type": "rate_limit",
 "is_transient": true,
 "retry_after_seconds": 60
 }
 }
}
```

---

## Setting Up MCP Servers

### Prerequisites

All servers:

- Python 3.11+
- Dependencies in requirements.txt
- Appropriate API keys or local setup

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Individual Server Setup

#### Anthropic

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python mcp-server/anthropic_mcp_server.py
```

#### OpenAI

```bash
export OPENAI_API_KEY="sk-proj-..."
python mcp-server/openai_mcp_server.py
```

#### Mistral

```bash
export MISTRAL_API_KEY="..."
python mcp-server/mistral_mcp_server.py
```

#### Google AI Studio

```bash
export GOOGLE_API_KEY="..."
python mcp-server/google_ai_studio_mcp_server.py
```

#### Ollama (Local)

```bash
ollama serve # In separate terminal
python mcp-server/ollama_mcp_server.py
```

#### Devstral Local

```bash
export MODEL_PATH="/path/to/devstral-24b"
python mcp-server/devstral_local_mcp_server.py
```

### Test Server Connectivity

```bash
# Start Hillstar with debug logging
HILLSTAR_DEBUG=1 hillstar run workflow.json

# Check server initialization logs
# Each server should print: "Provider ready: {provider}"
```

---

## Security Considerations

### Credential Handling

Each MCP Server:

1. Receives credentials via environment only
2. Validates credentials before use
3. Never logs or exports credentials
4. Returns credential errors without leaking details

Pattern:

```python
api_key = os.getenv(f"{PROVIDER}_API_KEY")
if not api_key:
 return error("API key not found. Run: hillstar config")
```

### Error Redaction

Errors from MCP servers are automatically redacted:

- Remove credential patterns (sk-ant-*, sk-proj-*, etc.)
- Remove sensitive header values
- Preserve technical error context
- Example: "Error: Invalid key sk-ant-..." becomes "Error: Invalid key [REDACTED:anthropic_key]"

### Subprocess Isolation

MCP servers run as isolated subprocesses:

- No access to main process memory
- No access to other credentials
- No access to other model instances
- Crash isolation: server crash doesn't crash orchestrator

### API Key Validation

Three-tier validation:

1. Check for presence (error if missing)
2. Check format (error if invalid)
3. Check validity (error on first API call)

### Rate Limiting and Quotas

Each server implements:

- Exponential backoff on rate limits
- Quota tracking per provider
- Fallback to alternate providers
- Cost limiting to prevent bill shock

---

## Troubleshooting

### Server Fails to Start

Check:

1. API key is set correctly
2. Python environment has dependencies
3. Port isn't already in use (Ollama)
4. Network connectivity to API endpoints

### Authentication Errors

Solutions:

1. Verify API key format
2. Check API key permissions (may need regeneration)
3. Confirm key is for correct environment (dev vs. prod)
4. Check for expired keys

### Slow Responses

Causes:

1. Network latency to API
2. Model processing time
3. Rate limiting with backoff
4. Overloaded provider

Solutions:

1. Use smaller model
2. Use local model (Ollama)
3. Reduce batch size
4. Implement timeouts

### Token/Cost Issues

Check:

1. Model context window (max_tokens)
2. Actual vs. estimated costs
3. Provider billing dashboard
4. Request token counts

---

## Custom MCP Servers

### Implementing a Custom Server

Template:

```python
import json
import sys
from typing import Any

class CustomMCPServer:
 def __init__(self):
 self.provider = "custom_provider"
 self.models = ["model-1", "model-2"]

 def initialize(self, api_key: str, config: dict) -> dict:
 # Validate and initialize
 return {
 "provider": self.provider,
 "models": self.models,
 "status": "ready"
 }

 def call(self, model: str, messages: list, **params) -> dict:
 # Call model and return response
 return {
 "content": "response",
 "stop_reason": "end_turn",
 "input_tokens": 10,
 "output_tokens": 5,
 "cost_usd": 0.01
 }

 def handle_request(self, request: dict) -> dict:
 method = request.get("method")
 params = request.get("params", {})

 if method == "initialize":
 result = self.initialize(**params)
 elif method == "call":
 result = self.call(**params)
 else:
 return {"error": f"Unknown method: {method}"}

 return {"result": result}

# Main loop
if __name__ == "__main__":
 server = CustomMCPServer()
 for line in sys.stdin:
 request = json.loads(line)
 response = server.handle_request(request)
 print(json.dumps(response))
 sys.stdout.flush()
```

### Registering Custom Server

1. Place server file in mcp-server/
2. Add to provider registry
3. Update model_selector.py to recognize provider
4. Test with sample workflow

---

## Testing MCP Servers

### Unit Tests

MCP error handling and model tests:

```bash
python -m pytest tests/test_models_mcp_error_handling.py -v
```

### E2E Tests

Test complete workflows with providers:

```bash
python -m pytest tests/test_e2e_connectivity.py -v
python -m pytest tests/test_e2e_haiku_synthesis.py -v
python -m pytest tests/test_e2e_local_execution.py -v
```

---

## Performance and Optimization

### Subprocess Overhead

MCP subprocess overhead:

- Startup: 100-500ms per provider (first use)
- Per-request: 10-50ms overhead
- Cached instances: No startup overhead

Optimization:

- Keep provider instances alive across calls
- Reuse same provider for multiple calls
- Use local Ollama for lowest latency

### Concurrent Requests

MCP servers handle concurrency via:

- Sequential request processing (per subprocess)
- Multiple provider instances for parallel calls
- Fallback providers if one is slow

### Resource Usage

Per subprocess:

- Memory: 50-200MB (Python interpreter)
- CPU: Minimal when idle
- Network: Only when calling APIs

---

## Version Compatibility

MCP Protocol Version: 2.0
Minimum Python: 3.11
SDK Versions (pinned in requirements.txt):

- anthropic: Latest
- openai: Latest
- mistral-sdk: Latest
- google-generativeai: Latest

---

**Document Status:** Sprint 1 Release
**Last Updated:** 2026-02-28
**Version:** 1.0.0

See PROVIDER_MODEL_REFERENCE.md for provider-specific details and capabilities.
