"""Pytest configuration for hillstar tests."""

import sys
from pathlib import Path

# Add parent directory to path so tests can import hillstar modules
sys.path.insert(0, str(Path(__file__).parent.parent))
