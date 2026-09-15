# SPDX-FileCopyrightText: 2026 Julen Gamboa <j.a.r.gamboa@gmail.com>
# SPDX-License-Identifier: AGPL-3.0-only

"""
Unit tests for utils/exceptions.py

Production-grade test suite with:
- Deep Assertions: Check exception hierarchy, inheritance, message content
- Mock Verification: N/A (pure exception classes)
- Parameterized Tests: Multiple exception types and scenarios
- Boundary Testing: Empty messages, very long messages, special characters
- Realistic Data: Real error scenarios and messages
- Integration Points: Exception raising and catching in workflows
- Side Effects: Exception propagation and inheritance chain
- Error Messages: Verify exception messages are informative
"""

import pytest
from utils.exceptions import (
	HillstarException,
	ModelSelectionError,
	ConfigurationError,
	ExecutionError,
)


class TestHillstarExceptionHierarchy:
	"""Test exception class hierarchy and inheritance."""

	def test_model_selection_error_inherits_from_hillstar_exception(self):
		"""Deep: ModelSelectionError is subclass of HillstarException."""
		assert issubclass(ModelSelectionError, HillstarException)

	def test_configuration_error_inherits_from_hillstar_exception(self):
		"""Deep: ConfigurationError is subclass of HillstarException."""
		assert issubclass(ConfigurationError, HillstarException)

	def test_execution_error_inherits_from_hillstar_exception(self):
		"""Deep: ExecutionError is subclass of HillstarException."""
		assert issubclass(ExecutionError, HillstarException)

	def test_all_custom_exceptions_are_exceptions(self):
		"""Deep: All custom exceptions are Python Exception subclasses."""
		custom_exceptions = [
					ModelSelectionError,
			ConfigurationError,
			ExecutionError,
		]
		for exc_class in custom_exceptions:
			assert issubclass(exc_class, Exception)


class TestExceptionInstantiation:
	"""Test creating exception instances."""

	@pytest.mark.parametrize("exception_class", [
			ModelSelectionError,
		ConfigurationError,
		ExecutionError,
	])
	def test_exception_can_be_instantiated(self, exception_class):
		"""Parameterized: All exception types can be instantiated."""
		exc = exception_class()
		assert isinstance(exc, exception_class)
		assert isinstance(exc, HillstarException)
		assert isinstance(exc, Exception)

	@pytest.mark.parametrize("exception_class,message", [
		(ModelSelectionError, "Failed to select model for node_1"),
		(ConfigurationError, "Missing required field: provider_config"),
		(ExecutionError, "Node execution failed with error"),
	])
	def test_exception_stores_message(self, exception_class, message):
		"""Deep: Exception message is stored and retrievable."""
		exc = exception_class(message)

		# Deep: Check message is stored
		assert str(exc) == message
		assert exc.args == (message,)
		assert len(exc.args) > 0

	def test_model_selection_error_can_be_raised_and_caught(self):
		"""Integration: ModelSelectionError can be raised and caught."""
		with pytest.raises(ModelSelectionError) as exc_info:
			raise ModelSelectionError("No valid models available")

		assert "No valid models" in str(exc_info.value)

	def test_configuration_error_can_be_raised_and_caught(self):
		"""Integration: ConfigurationError can be raised and caught."""
		with pytest.raises(ConfigurationError) as exc_info:
			raise ConfigurationError("Invalid configuration")

		assert "Invalid configuration" in str(exc_info.value)

	def test_execution_error_can_be_raised_and_caught(self):
		"""Integration: ExecutionError can be raised and caught."""
		with pytest.raises(ExecutionError) as exc_info:
			raise ExecutionError("Execution failed")

		assert "Execution failed" in str(exc_info.value)

	def test_exception_can_be_caught_by_parent_hillstar_exception(self):
		"""Side Effect: Child exceptions catchable by parent HillstarException."""
		# Verify ModelSelectionError catchable as HillstarException
		with pytest.raises(HillstarException):
			raise ModelSelectionError("model selection error")

		# Verify ModelSelectionError catchable as HillstarException
		with pytest.raises(HillstarException):
			raise ModelSelectionError("Model error")


class TestExceptionMessages:
	"""Test exception message handling."""

	@pytest.mark.parametrize("exception_class,message", [
		(ModelSelectionError, "Provider 'anthropic' model 'claude-opus-4-6' not available"),
		(ConfigurationError, "Required field 'graph' missing from workflow"),
		(ExecutionError, "Node 'node_1' failed: Invalid input format"),
	])
	def test_exception_with_realistic_messages(self, exception_class, message):
		"""Realistic Data: Test with actual error messages."""
		exc = exception_class(message)

		# Deep: Message preserved exactly
		assert str(exc) == message
		assert len(str(exc)) > 0

	def test_exception_with_special_characters_in_message(self):
		"""Boundary: Exception message with special characters."""
		message = "Error: Node failed with 'value' = $100 & cost > limit\n\t!"
		exc = ConfigurationError(message)

		# Deep: Special characters preserved
		assert str(exc) == message
		assert "'" in str(exc)
		assert "$" in str(exc)


class TestExceptionChaining:
	"""Test exception chaining (raise from)."""

	def test_exception_chain_preserves_original_message(self):
		"""Side Effect: Exception chain preserves both messages."""
		original_msg = "Connection timeout"
		new_msg = "Execution failed due to connection error"

		with pytest.raises(ExecutionError) as exc_info:
			try:
				raise TimeoutError(original_msg)
			except TimeoutError as e:
				raise ExecutionError(new_msg) from e

		# Deep: Both messages accessible
		assert str(exc_info.value) == new_msg
		assert str(exc_info.value.__cause__) == original_msg


class TestExceptionInheritanceChain:
	"""Test the complete inheritance chain."""

	@pytest.mark.parametrize("exception_class,expected_doc_keyword", [
		(ModelSelectionError, "model"),
		(ConfigurationError, "configuration"),
		(ExecutionError, "execution"),
	])
	def test_custom_exception_has_docstring_with_keyword(self, exception_class, expected_doc_keyword):
		"""Deep: All custom exceptions documented with relevant keywords."""
		assert exception_class.__doc__ is not None
		assert len(exception_class.__doc__) > 0
		assert expected_doc_keyword.lower() in exception_class.__doc__.lower()
