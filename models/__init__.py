"""LLM Model Provider Integrations for Hillstar Orchestrator.

Unified interface to multiple LLM providers with consistent credential handling
(environment variables only, no embedded keys).

Supported providers:
    - anthropic: Anthropic Claude (cloud API)
    - openai: OpenAI GPT (cloud API)
    - anthropic_ollama: Anthropic via Ollama (local proxy)
    - ollama: Local Ollama models
    - devstral_local: Devstral local (GPU required)
    - google_ai_studio: Google Gemini (API key auth)
    - mistral: Mistral AI (cloud API)
"""

# Phase 1 - Core provider integrations
from .anthropic_ollama_api_model import AnthropicOllamaAPIModel
from .anthropic_model import AnthropicModel
from .devstral_local_model import DevstralLocalModel
from .mistral_api_model import MistralAPIModel
from .mcp_model import MCPModel
from .anthropic_mcp_model import AnthropicMCPModel
from .openai_mcp_model import OpenAIMCPModel
from .mistral_mcp_model import MistralMCPModel
from .ollama_mcp_model import OllamaMCPModel

# Phase 2 (not included in v1.0.0)
# - local_model
# - google_ai_studio_model
# - google_vertex_model
# - azure_ai_model
# - amazon_bedrock_model
# - cohere_model
# - meta_llama_model

__all__ = [
	"AnthropicOllamaAPIModel",
	"AnthropicModel",
	"DevstralLocalModel",
	"MistralAPIModel",
	"MCPModel",
	"AnthropicMCPModel",
	"OpenAIMCPModel",
	"MistralMCPModel",
	"OllamaMCPModel",
]
