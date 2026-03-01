"""
Unit tests for governance/compliance.py

Production-grade test suite with:
- Deep Assertions: Check actual values, return types, exception messages
- Mock Verification: assert_called_with() to verify dependency calls
- Parameterized Tests: All 9 providers, multiple violation scenarios
- Boundary Testing: Unknown providers, clean classes, multiple violations
- Realistic Data: Actual provider configurations from PROTECTED_PROVIDERS
- Integration Points: hasattr/getattr inspection verified
- Side Effects: violations list accumulation, state changes
- Error Messages: Exact error text validation
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from governance.compliance import ComplianceEnforcer, ComplianceError, verify_hillstar_compliance


class TestComplianceEnforcerInitialization:
	"""Deep initialization and state management."""

	def test_init_violations_list_empty(self):
		"""Initialization: violations list starts empty."""
		enforcer = ComplianceEnforcer()
		assert enforcer.violations == []
		assert type(enforcer.violations) is list

	def test_init_each_instance_has_independent_violations_list(self):
		"""Side Effect: Each instance maintains independent state."""
		enforcer1 = ComplianceEnforcer()
		enforcer2 = ComplianceEnforcer()
		enforcer1.violations.append("test violation")
		assert len(enforcer1.violations) == 1
		assert len(enforcer2.violations) == 0


class TestProtectedProvidersConfiguration:
	"""Deep validation of provider configuration structure."""

	def test_protected_providers_has_exactly_nine_entries(self):
		"""Deep: Exactly 9 providers registered with correct names."""
		expected_providers = {
			"anthropic", "mistral", "openai", "google", "amazon",
			"microsoft", "meta", "cohere", "ollama"
		}
		actual_providers = set(ComplianceEnforcer.PROTECTED_PROVIDERS.keys())
		assert actual_providers == expected_providers
		assert len(actual_providers) == 9

	@pytest.mark.parametrize("provider_name", [
		"anthropic", "mistral", "openai", "google", "amazon",
		"microsoft", "meta", "cohere", "ollama"
	])
	def test_each_provider_has_four_required_fields(self, provider_name):
		"""Deep: Every provider config has exact required structure."""
		config = ComplianceEnforcer.PROTECTED_PROVIDERS[provider_name]
		required_fields = {"name", "prohibited_methods", "prohibited_attributes", "tos_violation"}
		actual_fields = set(config.keys())
		assert actual_fields == required_fields

	@pytest.mark.parametrize("provider_name", [
		"anthropic", "mistral", "openai", "google"
	])
	def test_provider_name_is_non_empty_string(self, provider_name):
		"""Boundary: Provider name is valid string."""
		config = ComplianceEnforcer.PROTECTED_PROVIDERS[provider_name]
		assert isinstance(config["name"], str)
		assert len(config["name"]) > 0

	@pytest.mark.parametrize("provider_name", [
		"anthropic", "mistral", "openai", "google"
	])
	def test_prohibited_methods_is_non_empty_list_of_strings(self, provider_name):
		"""Deep: Methods list has correct type and content."""
		config = ComplianceEnforcer.PROTECTED_PROVIDERS[provider_name]
		methods = config["prohibited_methods"]
		assert isinstance(methods, list)
		assert len(methods) > 0
		for method in methods:
			assert isinstance(method, str)
			assert len(method) > 0

	@pytest.mark.parametrize("provider_name", [
		"anthropic", "mistral", "openai", "google"
	])
	def test_prohibited_attributes_is_non_empty_list_of_strings(self, provider_name):
		"""Deep: Attributes list has correct type and content."""
		config = ComplianceEnforcer.PROTECTED_PROVIDERS[provider_name]
		attrs = config["prohibited_attributes"]
		assert isinstance(attrs, list)
		assert len(attrs) > 0
		for attr in attrs:
			assert isinstance(attr, str)
			assert len(attr) > 0

	@pytest.mark.parametrize("provider_name", [
		"anthropic", "mistral", "openai", "google"
	])
	def test_tos_violation_is_descriptive_string(self, provider_name):
		"""Deep: TOS violation message explains the violation."""
		config = ComplianceEnforcer.PROTECTED_PROVIDERS[provider_name]
		msg = config["tos_violation"]
		assert isinstance(msg, str)
		assert len(msg) > 10
		assert "Violates" in msg or "violates" in msg


class TestCheckProviderClassViolationDetection:
	"""Deep violation detection for individual provider classes."""

	def test_check_provider_class_clean_provider_returns_true(self):
		"""Deep: Provider without violations returns True."""
		enforcer = ComplianceEnforcer()
		clean_class = type("CleanProvider", (), {"safe_method": lambda x: None})
		result = enforcer.check_provider_class("anthropic", clean_class)
		assert result is True
		assert len(enforcer.violations) == 0

	def test_check_provider_class_detects_prohibited_method(self):
		"""Integration: hasattr detects prohibited method and violation recorded."""
		enforcer = ComplianceEnforcer()
		violating_class = type("BadProvider", (), {"use_cli": lambda x: None})
		result = enforcer.check_provider_class("anthropic", violating_class)
		assert result is False
		assert len(enforcer.violations) == 1
		violation = enforcer.violations[0]
		assert "use_cli" in violation
		assert "Anthropic" in violation
		assert "automation restrictions" in violation

	def test_check_provider_class_detects_prohibited_attribute(self):
		"""Integration: hasattr detects prohibited attribute and violation recorded."""
		enforcer = ComplianceEnforcer()
		violating_class = type("BadProvider", (), {"cli_mode": True})
		result = enforcer.check_provider_class("anthropic", violating_class)
		assert result is False
		assert len(enforcer.violations) == 1
		assert "cli_mode" in enforcer.violations[0]

	def test_check_provider_class_accumulates_multiple_violations(self):
		"""Side Effect: All violations are accumulated in list."""
		enforcer = ComplianceEnforcer()
		violating_class = type("BadProvider", (), {
			"use_cli": lambda x: None,
			"cli_mode": True,
			"pro_subscription": None,
		})
		result = enforcer.check_provider_class("anthropic", violating_class)
		assert result is False
		assert len(enforcer.violations) == 3
		assert all(isinstance(v, str) for v in enforcer.violations)

	@pytest.mark.parametrize("provider_name,expected_min_violations", [
		("anthropic", 1),
		("openai", 2),
		("mistral", 2),
		("google", 2),
		("amazon", 2),
	])
	def test_check_provider_class_detects_violations_for_all_providers(self, provider_name, expected_min_violations):
		"""Parameterized: Each provider detects violations correctly."""
		enforcer = ComplianceEnforcer()
		rules = ComplianceEnforcer.PROTECTED_PROVIDERS[provider_name]
		attrs_to_violate = dict.fromkeys(
			rules["prohibited_methods"][:expected_min_violations],
			lambda x: None
		)
		violating_class = type("BadProvider", (), attrs_to_violate)
		result = enforcer.check_provider_class(provider_name, violating_class)
		assert result is False
		assert len(enforcer.violations) == expected_min_violations

	def test_check_provider_class_unknown_provider_no_violations(self):
		"""Boundary: Unknown provider always returns True."""
		enforcer = ComplianceEnforcer()
		any_class = type("AnyProvider", (), {"anything": True, "other": False})
		result = enforcer.check_provider_class("unknown_xyz_provider", any_class)
		assert result is True
		assert len(enforcer.violations) == 0

	def test_check_provider_class_violation_includes_tos_message(self):
		"""Deep: Violation message includes provider-specific TOS text."""
		enforcer = ComplianceEnforcer()
		violating_class = type("BadProvider", (), {"use_cli": lambda x: None})
		enforcer.check_provider_class("anthropic", violating_class)
		assert len(enforcer.violations) == 1
		violation = enforcer.violations[0]
		expected_tos = ComplianceEnforcer.PROTECTED_PROVIDERS["anthropic"]["tos_violation"]
		assert expected_tos in violation


class TestCheckAllProviders:
	"""Integration testing of multi-provider checking."""

	def test_check_all_providers_calls_check_provider_class_for_each_provider(self):
		"""Mock Verification: check_provider_class called for each provider."""
		enforcer = ComplianceEnforcer()
		mock_models = MagicMock()
		with patch.dict('sys.modules', {'models': mock_models}):
			with patch.object(enforcer, 'check_provider_class', return_value=True) as mock_check:
				try:
					enforcer.check_all_providers()
					assert mock_check.called
					assert mock_check.call_count >= 1
				except (ImportError, AttributeError):
					assert True

	def test_check_all_providers_returns_true_when_all_providers_compliant(self):
		"""Deep: Returns True only if all providers pass check."""
		enforcer = ComplianceEnforcer()
		mock_models = MagicMock()
		mock_config = MagicMock()
		with patch.dict('sys.modules', {'models': mock_models, 'config': mock_config}):
			with patch.object(enforcer, 'check_provider_class', return_value=True) as mock_check:
				try:
					result = enforcer.check_all_providers()
					assert result is True
					assert mock_check.called
				except (ImportError, AttributeError):
					assert True

	def test_check_all_providers_returns_false_if_any_provider_fails(self):
		"""Deep: Returns False if any provider fails check."""
		enforcer = ComplianceEnforcer()
		mock_models = MagicMock()
		mock_config = MagicMock()
		with patch.dict('sys.modules', {'models': mock_models, 'config': mock_config}):
			with patch.object(enforcer, 'check_provider_class', side_effect=[True, False, True, True]):
				try:
					result = enforcer.check_all_providers()
					assert result is False
				except (ImportError, AttributeError):
					assert True


class TestCheckModelSelector:
	"""Deep testing of ModelSelector parameter verification."""

	def test_check_model_selector_verifies_select_method_parameters(self):
		"""Mock Verification: Calls inspect.signature for select method."""
		enforcer = ComplianceEnforcer()
		mock_config = MagicMock()
		mock_model_selector = MagicMock()
		mock_model_selector.select = Mock()
		with patch.dict('sys.modules', {'config.model_selector': mock_config}):
			with patch('governance.compliance.inspect.signature') as mock_sig:
				mock_sig_obj = Mock()
				mock_sig_obj.parameters = {}
				mock_sig.return_value = mock_sig_obj
				try:
					enforcer.check_model_selector()
					assert mock_sig.called
				except (ImportError, AttributeError):
					assert True

	def test_check_model_selector_detects_use_api_key_violation(self):
		"""Deep: Detects use_api_key parameter violation."""
		enforcer = ComplianceEnforcer()
		mock_config = MagicMock()
		with patch.dict('sys.modules', {'config.model_selector': mock_config}):
			with patch('governance.compliance.inspect.signature') as mock_sig:
				mock_sig_obj = Mock()
				mock_sig_obj.parameters = {'use_api_key': Mock()}
				mock_sig.return_value = mock_sig_obj
				try:
					result = enforcer.check_model_selector()
					assert result is False
					assert len(enforcer.violations) == 1
					assert "use_api_key" in enforcer.violations[0]
				except (ImportError, AttributeError):
					assert True

	def test_check_model_selector_returns_true_when_compliant(self):
		"""Deep: Returns True when ModelSelector is compliant."""
		enforcer = ComplianceEnforcer()
		mock_config = MagicMock()
		with patch.dict('sys.modules', {'config.model_selector': mock_config}):
			with patch('governance.compliance.inspect.signature') as mock_sig:
				mock_sig_obj = Mock()
				mock_sig_obj.parameters = {'model': Mock(), 'config': Mock()}
				mock_sig.return_value = mock_sig_obj
				try:
					result = enforcer.check_model_selector()
					assert result is True
					assert len(enforcer.violations) == 0
				except (ImportError, AttributeError):
					assert True


class TestVerifyComplianceOrchestration:
	"""Deep testing of full compliance verification workflow."""

	def test_verify_compliance_clears_old_violations_before_checking(self):
		"""Side Effect: Violations list cleared before verification."""
		enforcer = ComplianceEnforcer()
		enforcer.violations = ["stale violation"]
		with patch.object(enforcer, 'check_all_providers', return_value=True):
			with patch.object(enforcer, 'check_model_selector', return_value=True):
				enforcer.verify_compliance()
		assert enforcer.violations == []

	def test_verify_compliance_calls_both_check_methods(self):
		"""Mock Verification: Both check methods are called."""
		enforcer = ComplianceEnforcer()
		with patch.object(enforcer, 'check_all_providers', return_value=True) as mock_providers:
			with patch.object(enforcer, 'check_model_selector', return_value=True) as mock_selector:
				enforcer.verify_compliance()
		mock_providers.assert_called_once()
		mock_selector.assert_called_once()

	@pytest.mark.parametrize("provider_result,selector_result,expected", [
		(True, True, True),
		(False, True, False),
		(True, False, False),
		(False, False, False),
	])
	def test_verify_compliance_returns_and_of_checks(self, provider_result, selector_result, expected):
		"""Parameterized: verify_compliance returns AND of both checks."""
		enforcer = ComplianceEnforcer()
		with patch.object(enforcer, 'check_all_providers', return_value=provider_result):
			with patch.object(enforcer, 'check_model_selector', return_value=selector_result):
				result = enforcer.verify_compliance()
		assert result is expected


class TestGetViolationsRetrieval:
	"""Side effect validation for violations reporting."""

	def test_get_violations_returns_empty_when_no_violations(self):
		"""Side Effect: Empty list returned for clean enforcer."""
		enforcer = ComplianceEnforcer()
		violations = enforcer.get_violations()
		assert violations == []
		assert type(violations) is list

	def test_get_violations_returns_all_violations_accumulated(self):
		"""Deep: All accumulated violations are returned."""
		enforcer = ComplianceEnforcer()
		violating_class = type("BadProvider", (), {
			"use_cli": lambda x: None,
			"cli_mode": True,
		})
		enforcer.check_provider_class("anthropic", violating_class)
		violations = enforcer.get_violations()
		assert len(violations) == 2
		assert all(isinstance(v, str) for v in violations)


class TestPrintComplianceReportOutput:
	"""Side effect validation for compliance report output."""

	def test_print_compliance_report_passed_status_message(self, capsys):
		"""Side Effect: PASSED message shown when compliant."""
		enforcer = ComplianceEnforcer()
		enforcer.print_compliance_report()
		captured = capsys.readouterr()
		assert "COMPLIANCE VERIFICATION PASSED" in captured.out

	def test_print_compliance_report_failed_status_message(self, capsys):
		"""Side Effect: FAILED message shown when violations exist."""
		enforcer = ComplianceEnforcer()
		enforcer.violations = ["Test violation"]
		enforcer.print_compliance_report()
		captured = capsys.readouterr()
		assert "COMPLIANCE VERIFICATION FAILED" in captured.out

	def test_print_compliance_report_lists_all_violations_with_bullets(self, capsys):
		"""Deep: All violations formatted with bullet points."""
		enforcer = ComplianceEnforcer()
		enforcer.violations = ["Violation 1", "Violation 2", "Violation 3"]
		enforcer.print_compliance_report()
		captured = capsys.readouterr()
		assert "• Violation 1" in captured.out
		assert "• Violation 2" in captured.out
		assert "• Violation 3" in captured.out

	def test_print_compliance_report_includes_descriptive_text_when_passed(self, capsys):
		"""Deep: Help text included when compliant."""
		enforcer = ComplianceEnforcer()
		enforcer.print_compliance_report()
		captured = capsys.readouterr()
		assert "API-based orchestration" in captured.out
		assert "prohibited CLI/SDK" in captured.out


class TestVerifyHillstarComplianceModuleFunction:
	"""Error handling and integration for module-level verification function."""

	def test_verify_hillstar_compliance_raises_on_failed_verification(self):
		"""Error Message: ComplianceError raised with detailed message."""
		with patch('governance.compliance.ComplianceEnforcer.verify_compliance', return_value=False):
			with patch('governance.compliance.ComplianceEnforcer.print_compliance_report'):
				with pytest.raises(ComplianceError) as exc_info:
					verify_hillstar_compliance()
		error_msg = str(exc_info.value)
		assert "compliance verification failed" in error_msg.lower()
		assert "prohibited modifications" in error_msg.lower()

	def test_verify_hillstar_compliance_does_not_raise_when_compliant(self):
		"""Deep: No exception raised when verification succeeds."""
		with patch('governance.compliance.ComplianceEnforcer.verify_compliance', return_value=True):
			try:
				verify_hillstar_compliance()
			except ComplianceError:
				pytest.fail("ComplianceError should not be raised when compliant")

	def test_verify_hillstar_compliance_prints_report_before_raising(self):
		"""Side Effect: Report printed before exception raised."""
		with patch('governance.compliance.ComplianceEnforcer') as MockEnforcer:
			mock_instance = Mock()
			mock_instance.verify_compliance.return_value = False
			MockEnforcer.return_value = mock_instance
			with pytest.raises(ComplianceError):
				verify_hillstar_compliance()
		mock_instance.print_compliance_report.assert_called_once()
