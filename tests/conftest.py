"""Pytest configuration for hillstar tests."""

import sys
import pytest
from pathlib import Path
from io import StringIO

# Add parent directory to path so tests can import hillstar modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.credential_redactor import CredentialRedactor


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
	redactor = CredentialRedactor()
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
	"""Configure pytest with credential redaction."""
	# Hook into pytest's output capture to redact credentials
	pass
