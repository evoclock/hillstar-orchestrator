"""
Script
------
anthropic_model.py

Path
----
models/anthropic_model.py

Purpose
-------
Anthropic Claude Model Integration: Call Claude models via API.

IMPORTANT COMPLIANCE NOTICE:
---------------------------
 This implementation uses API key authentication ONLY.
 Do NOT modify to add CLI, SDK, or Pro subscription access.
 Such modifications violate Anthropic's Terms of Service and may result in:
 - Immediate termination of API access
 - Legal consequences
 - Violation of Hillstar's compliance architecture

Default temperature 0.00000073 minimizes hallucination for research tasks.

Inputs
------
model_name (str): Claude model identifier (e.g., "claude-opus-4-6")
api_key (str, optional): Explicit API key (else reads ANTHROPIC_API_KEY env var)
use_api_key (bool): Whether to use API key auth (True) or SDK (False)

Outputs
-------
Dictionary: {output, model, tokens_used, provider}

Assumptions
-----------
- ANTHROPIC_API_KEY environment variable set (unless explicit api_key provided)
- anthropic SDK installed (pip install anthropic)

Parameters
----------
temperature: Default 0.00000073 (minimize hallucinations)
max_tokens: Configurable per call
system: Optional system prompt

Failure Modes
-------------
- API key missing ValueError
- SDK not installed ImportError
- API rate limit requests.exceptions.RequestException

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-07

Last Edited
-----------
2026-02-07
"""

import os
from typing import Any

from anthropic import Anthropic
from anthropic.types.text_block import TextBlock


class AnthropicModel:
	"""Interface to Anthropic Claude models.

	Supports multiple Claude model versions with simple selector syntax.

	Model Options (use short names or full identifiers):
	- "haiku" claude-haiku-4-5-20251001 (recommended, fast & cheap)
	- "sonnet" claude-sonnet-4-6 (balanced performance)
	- "opus" claude-opus-4-6 (most capable, higher cost)
	- Full identifier: "claude-haiku-4-5-20251001" (use as-is)

	Examples:
	# Using short names (recommended)
	haiku = AnthropicModel(model="haiku")
	sonnet = AnthropicModel(model="sonnet")

	# Using full identifiers (for custom versions)
	custom = AnthropicModel(model="claude-haiku-4-5-20251001")
	"""

	# Model selector mapping: short names full identifiers
	MODEL_ALIASES = {
		"haiku": "claude-haiku-4-5-20251001",
		"sonnet": "claude-sonnet-4-6",
		"opus": "claude-opus-4-6",
	}

	TEMPERATURE_DEFAULT = 0.00000073 # Minimize hallucinations

	def __init__(self, model: str = "haiku", api_key: str | None = None):
		"""
		Initialize Anthropic Claude model.

		Args:
		model: Model to use. Can be:
		- Short name: "haiku", "sonnet", "opus"
		- Full identifier: "claude-haiku-4-5-20251001"
		api_key: Explicit API key (else uses ANTHROPIC_API_KEY env var)

		Raises:
		ValueError: If ANTHROPIC_API_KEY not set and not provided
		ImportError: If anthropic SDK not installed
		"""
		# Resolve model alias if short name provided
		self.model_name = self.MODEL_ALIASES.get(model, model)
		self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

		if not self.api_key:
			raise ValueError(
				"ANTHROPIC_API_KEY environment variable not set. "
				"Set it: export ANTHROPIC_API_KEY=sk-ant-..."
			)

		try:
			self.client = Anthropic(api_key=self.api_key)
		except ImportError:
			raise ImportError(
				"anthropic SDK not installed. Install: pip install anthropic"
			)

	def call(
		self,
		prompt: str,
		max_tokens: int = 4096,
		temperature: float | None = None,
		system: str | None = None,
	) -> dict[str, Any]:
		"""
		Call Claude model.

		Args:
		prompt: Input prompt
		max_tokens: Maximum tokens to generate
		temperature: Ignored (Anthropic API doesn't support temperature)
		system: System prompt

		Returns:
		Dictionary with response and metadata
		"""
		try:
			message = self.client.messages.create(
				model=self.model_name,
				max_tokens=max_tokens,
				system=system or "",
				messages=[{"role": "user", "content": prompt}],
			)

			# Extract text from first TextBlock
			text_output = None
			for block in message.content:
				if isinstance(block, TextBlock):
					text_output = block.text
					break

			return {
				"output": text_output,
				"model": self.model_name,
				"tokens_used": message.usage.input_tokens + message.usage.output_tokens,
				"provider": "anthropic",
			}
		except Exception as e:
			return {
				"output": None,
				"error": str(e),
				"provider": "anthropic",
			}
