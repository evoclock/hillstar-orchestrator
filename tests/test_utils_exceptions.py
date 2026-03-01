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
	BudgetExceededError,
	ModelSelectionError,
	ConfigurationError,
	ExecutionError,
)


class TestHillstarExceptionHierarchy:
	"""Test exception class hierarchy and inheritance."""

	def test_budget_exceeded_inherits_from_hillstar_exception(self):
		"""Deep: BudgetExceededError is subclass of HillstarException."""
		assert issubclass(BudgetExceededError, HillstarException)
		assert issubclass(BudgetExceededError, Exception)

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
			BudgetExceededError,
			ModelSelectionError,
			ConfigurationError,
			ExecutionError,
		]
		for exc_class in custom_exceptions:
			assert issubclass(exc_class, Exception)


class TestExceptionInstantiation:
	"""Test creating exception instances."""

	@pytest.mark.parametrize("exception_class", [
		BudgetExceededError,
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
		(BudgetExceededError, "Budget exceeded: $50.00 limit reached"),
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

	def test_exception_with_empty_message(self):
		"""Boundary: Exception with empty string message."""
		exc = BudgetExceededError("")

		# Deep: Empty message is valid
		assert str(exc) == ""
		assert exc.args == ("",)


class TestExceptionRaising:
	"""Test raising and catching exceptions."""

	def test_budget_exceeded_can_be_raised_and_caught(self):
		"""Integration: BudgetExceededError can be raised and caught."""
		with pytest.raises(BudgetExceededError) as exc_info:
			raise BudgetExceededError("Limit exceeded")

		# Deep: Check caught exception details
		assert isinstance(exc_info.value, BudgetExceededError)
		assert "Limit exceeded" in str(exc_info.value)

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
		# Verify BudgetExceededError catchable as HillstarException
		with pytest.raises(HillstarException):
			raise BudgetExceededError("Budget error")

		# Verify ModelSelectionError catchable as HillstarException
		with pytest.raises(HillstarException):
			raise ModelSelectionError("Model error")


class TestExceptionMessages:
	"""Test exception message handling."""

	@pytest.mark.parametrize("exception_class,message", [
		(BudgetExceededError, "Workflow cost $150.00 exceeds limit of $100.00"),
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

	@pytest.mark.parametrize("message_length", [1, 50, 500, 5000])
	def test_exception_with_different_message_lengths(self, message_length):
		"""Boundary: Test exceptions with various message lengths."""
		message = "x" * message_length
		exc = BudgetExceededError(message)

		# Deep: All lengths supported
		assert len(str(exc)) == message_length
		assert str(exc) == message

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

	def test_exception_can_be_chained_from_another(self):
		"""Integration: Exception can be raised from another exception."""
		original_error = ValueError("Original error")

		with pytest.raises(BudgetExceededError) as exc_info:
			try:
				raise original_error
			except ValueError as e:
				raise BudgetExceededError("Budget check failed") from e

		# Deep: Chaining information preserved
		assert exc_info.value.__cause__ is original_error
		assert isinstance(exc_info.value.__cause__, ValueError)

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

	def test_budget_exceeded_inheritance_chain(self):
		"""Deep: BudgetExceededError has correct MRO (Method Resolution Order)."""
		exc = BudgetExceededError("test")

		# Deep: Check inheritance chain
		mro = type(exc).__mro__
		assert BudgetExceededError in mro
		assert HillstarException in mro
		assert Exception in mro
		assert BaseException in mro

	def test_all_custom_exceptions_proper_inheritance(self):
		"""Deep: All custom exceptions have proper inheritance chain."""
		custom_exceptions = [
			BudgetExceededError(),
			ModelSelectionError(),
			ConfigurationError(),
			ExecutionError(),
		]

		for exc in custom_exceptions:
			# Deep: All are HillstarException and Exception
			assert isinstance(exc, HillstarException)
			assert isinstance(exc, Exception)
			assert isinstance(exc, BaseException)


class TestExceptionEquality:
	"""Test exception equality and comparison."""

	def test_exceptions_with_same_message_are_equivalent(self):
		"""Deep: Two exceptions with same message are structurally equivalent."""
		exc1 = BudgetExceededError("Same message")
		exc2 = BudgetExceededError("Same message")

		# Deep: Same type and message
		assert type(exc1) is type(exc2)
		assert str(exc1) == str(exc2)
		assert exc1.args == exc2.args

	def test_exceptions_with_different_messages_are_not_equivalent(self):
		"""Deep: Exceptions with different messages differ."""
		exc1 = BudgetExceededError("Message 1")
		exc2 = BudgetExceededError("Message 2")

		# Deep: Different messages
		assert str(exc1) != str(exc2)
		assert exc1.args != exc2.args

	def test_different_exception_types_not_equivalent(self):
		"""Deep: Different exception types are not equivalent."""
		exc1 = BudgetExceededError("Error")
		exc2 = ModelSelectionError("Error")

		# Deep: Different types
		assert type(exc1) is not type(exc2)
		assert not isinstance(exc1, ModelSelectionError)
		assert not isinstance(exc2, BudgetExceededError)


class TestExceptionDocumentation:
	"""Test that exceptions have proper docstrings."""

	def test_hillstar_exception_has_docstring(self):
		"""Deep: HillstarException has documentation."""
		assert HillstarException.__doc__ is not None
		assert len(HillstarException.__doc__) > 0
		assert "Base exception" in HillstarException.__doc__

	@pytest.mark.parametrize("exception_class,expected_doc_keyword", [
		(BudgetExceededError, "Budget"),
		(ModelSelectionError, "model"),
		(ConfigurationError, "configuration"),
		(ExecutionError, "execution"),
	])
	def test_custom_exception_has_docstring_with_keyword(self, exception_class, expected_doc_keyword):
		"""Deep: All custom exceptions documented with relevant keywords."""
		assert exception_class.__doc__ is not None
		assert len(exception_class.__doc__) > 0
		assert expected_doc_keyword.lower() in exception_class.__doc__.lower()
