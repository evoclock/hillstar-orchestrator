#!/usr/bin/env python3
"""Secure logging module for MCP servers.

Implements three-tier logging:
1. AUDIT - Safe metadata, never contains sensitive data
2. DEBUG - Development info with redacted details
3. MEMORY - In-memory debugging (never persisted to disk)

Usage:
 from secure_logger import get_logger
 logger = get_logger(__name__)

 logger.audit("Task completed successfully")
 logger.debug_redacted("Response", len(response))
 logger.memory_only("Full prompt details", prompt[:100])
"""

import logging
import os
from pathlib import Path


class SecureLogger(logging.Logger):
	"""Custom logger that prevents accidental sensitive data logging."""

	def __init__(self, name):
		super().__init__(name)
		self.debug_mode = os.getenv("MCP_DEBUG", "").lower() == "true"

	def audit(self, message, *args, **kwargs):
		"""Log safe audit information.

		Use for: actions, status, error codes, model names
		NEVER: prompts, responses, API keys, full exceptions
		"""
		self.info(f"[AUDIT] {message}", *args, **kwargs)

	def debug_redacted(self, label, *redacted_values, **kwargs):
		"""Log debug info with redacted sensitive values.

		Example:
		logger.debug_redacted("Response", len(response), "bytes")
		# Output: [DEBUG] Response: 342 bytes

		NOT:
		logger.debug_redacted("Response", response) # Would include full data
		"""
		if self.isEnabledFor(logging.DEBUG):
			msg = f"[DEBUG] {label}: {' '.join(str(v) for v in redacted_values)}"
			self.debug(msg, **kwargs)

	def memory_only(self, label, value):
		"""Log to memory ONLY (for debugging during execution).

		NOT written to disk. Only available while process is running.
		Useful for development/debugging to see full values.

		Example:
		logger.memory_only("Prompt", prompt) # Full prompt in memory only
		"""
		if self.debug_mode:
			# Print to stderr (not captured by file handlers)
			import sys
			print(f"[MEMORY] {label}: {str(value)[:500]}", file=sys.stderr)

	def error_safe(self, message, exception=None):
		"""Log errors without exposing exception details.

		Use this instead of:
		logger.error(f"Error: {e}") # BAD - e might contain API key

		Use instead:
		logger.error_safe("API call failed", e) # GOOD - exception hidden
		"""
		self.error(f"[ERROR] {message}")
		if self.debug_mode and exception:
			# Only log exception details in debug mode
			self.debug(f"Exception type: {type(exception).__name__}")


# Configure logging
def setup_secure_logging(log_dir=None, debug=False):
	"""Set up secure logging for all MCP servers.

	Args:
	log_dir: Directory for audit logs (default: ~/.hillstar/mcp-logs)
	debug: Enable debug logging (default: False)
	"""
	if log_dir is None:
		log_dir = Path.home() / ".hillstar" / "mcp-logs"

	log_dir.mkdir(parents=True, exist_ok=True)

	# Set custom logger class
	logging.setLoggerClass(SecureLogger)

	# Create formatters
	audit_formatter = logging.Formatter(
		'%(asctime)s - %(name)s - %(levelname)s - %(message)s'
	)

	# File handler: AUDIT LOGS ONLY (safe to persist)
	audit_handler = logging.FileHandler(log_dir / "mcp.log")
	audit_handler.setLevel(logging.INFO)
	audit_handler.setFormatter(audit_formatter)

	# Console handler: DEBUG info during development
	if debug or os.getenv("MCP_DEBUG"):
		console_handler = logging.StreamHandler()
		console_handler.setLevel(logging.DEBUG)
		console_handler.setFormatter(audit_formatter)

		root_logger = logging.getLogger()
		root_logger.addHandler(console_handler)
		root_logger.setLevel(logging.DEBUG)

	# Add file handler
	root_logger = logging.getLogger()
	root_logger.addHandler(audit_handler)
	root_logger.setLevel(logging.INFO)


def get_logger(name):
	"""Get a secure logger instance.

	Usage:
	from secure_logger import get_logger
	logger = get_logger(__name__)

	logger.audit("Task started")
	logger.debug_redacted("Response size", len(response), "bytes")
	logger.error_safe("API failed", exception)
	"""
	return logging.getLogger(name)
