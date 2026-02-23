"""
Script
------
exceptions.py

Path
----
python/hillstar/exceptions.py

Purpose
-------
Custom exceptions for Hillstar Orchestrator.

Provides domain-specific exceptions for error handling:
- BudgetExceededError: Workflow exceeded cost limits
- ModelSelectionError: Failed to select valid model
- ConfigurationError: Invalid workflow configuration

Author: Julen Gamboa <julen.gamboa.ds@gmail.com>

Created
-------
2026-02-07

Last Edited
-----------
2026-02-07
"""


class HillstarException(Exception):
	"""Base exception for Hillstar Orchestrator."""
	pass


class BudgetExceededError(HillstarException):
	"""Raised when workflow cost exceeds budget limits."""
	pass


class ModelSelectionError(HillstarException):
	"""Raised when model selection fails."""
	pass


class ConfigurationError(HillstarException):
	"""Raised when workflow configuration is invalid."""
	pass


class ExecutionError(HillstarException):
	"""Raised when node execution fails."""
	pass
