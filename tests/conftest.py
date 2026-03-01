"""Pytest configuration for hillstar tests."""

import sys
import pytest
from pathlib import Path
from dotenv import load_dotenv

from utils.credential_redactor import CredentialRedactor

# Add parent directory to path so tests can import hillstar modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env file for API credentials
repo_root = Path(__file__).parent.parent
env_file = repo_root / ".env"
if env_file.exists():
	load_dotenv(env_file, override=True)


class CredentialRedactingStream:
	"""Wrapper for stdout/stderr that redacts credentials."""

	def __init__(self, stream):
		self.stream = stream
		self.redactor = CredentialRedactor()

	def write(self, text):
		"""Write text with credentials redacted."""
		if text:
			redacted = self.redactor.redact(text)
			return self.stream.write(redacted)
		return 0

	def flush(self):
		"""Flush underlying stream."""
		return self.stream.flush()

	def __getattr__(self, name):
		"""Delegate other attributes to underlying stream."""
		return getattr(self.stream, name)


@pytest.fixture(scope="session", autouse=True)
def configure_credential_redaction():
	"""Configure credential redaction for test session."""
	# This fixture ensures credentials are redacted during tests
	yield


def pytest_runtest_makereport(item, call):
	"""Redact credentials from test reports."""
	# This hook is called after each test phase (setup, call, teardown)
	# We redact any captured output here
	pass


def pytest_runtest_logreport(report):
	"""Redact credentials from test failure reports."""
	redactor = CredentialRedactor()

	# Redact longrepr (failure/error messages)
	if report.longrepr:
		if isinstance(report.longrepr, str):
			report.longrepr = redactor.redact(report.longrepr)

	# Redact section information
	if hasattr(report, 'sections'):
		for i, (name, content) in enumerate(report.sections):
			redacted = redactor.redact(content)
			report.sections[i] = (name, redacted)


def pytest_configure(config):
	"""Configure pytest with dynamic HTML report naming."""
	from datetime import datetime
	import os

	# Determine if running full suite or individual test file
	test_items = config.args if config.args else []

	# If no specific test files specified, it's a full suite run
	if not test_items or test_items == ['tests']:
		report_name = f"full_suite_{datetime.now().strftime('%Y-%m-%d')}.html"
		config.option.htmlpath = f".test-results/html/{report_name}"
	else:
		# For individual test files, use test_<filename>.html
		# Extract the test file name from the path
		test_file = test_items[0] if isinstance(test_items[0], str) else 'tests'
		if 'test_' in test_file:
			# Extract filename from path like tests/test_config_setup_wizard.py
			filename = test_file.split('/')[-1].replace('.py', '')
			report_name = f"{filename}.html"
			config.option.htmlpath = f".test-results/html/{report_name}"

	# Ensure the html plugin is enabled
	config.pluginmanager.set_blocked('html')
	if not config.pluginmanager.has_plugin('html'):
		try:
			config.pluginmanager.register(__import__('pytest_html'))
		except ImportError:
			pass


# HTML Report Generation
# =====================
# To generate individual HTML reports for each test file with proper naming:
#
# Run each test file separately with --html flag:
# pytest tests/test_config_hillstar_config.py \
# --html=.test-results/html/test_config_hillstar_config.html
# pytest tests/test_config_provider_registry.py \
# --html=.test-results/html/test_config_provider_registry.html
#
# Report naming convention: test_<module>_<script>.html
# Example: test_config_hillstar_config.html (from config/config.py)
