#!/usr/bin/env python3
"""
Test script for Chrome Monitor Tool
Validates environment, dependencies, CLI behavior, and CDP connectivity.
"""

import os
import subprocess
import sys
import unittest

SCRIPT_PATH = os.path.join(
    os.path.dirname(__file__),
    ".agents", "skills", "chrome-monitor", "scripts", "chrome_inspector.py"
)
PYTHON_BIN = os.path.join(os.path.dirname(__file__), ".venv", "bin", "python")

class TestChromeMonitorSetup(unittest.TestCase):

    def test_script_exists(self):
        """Verify chrome_inspector.py is present."""
        self.assertTrue(os.path.exists(SCRIPT_PATH), f"Script not found at {SCRIPT_PATH}")

    def test_imports(self):
        """Verify required modules can be imported inside the virtual environment."""
        result = subprocess.run(
            [PYTHON_BIN, "-c", "import playwright; import requests; print('IMPORTS_OK')"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, f"Import error: {result.stderr}")
        self.assertIn("IMPORTS_OK", result.stdout)

    def test_cli_help(self):
        """Verify CLI help output."""
        result = subprocess.run(
            [PYTHON_BIN, SCRIPT_PATH, "--help"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Chrome Inspector for Antigravity & Claude Code", result.stdout)

    def test_check_command(self):
        """Verify the 'check' command runs cleanly and returns structured output."""
        result = subprocess.run(
            [PYTHON_BIN, SCRIPT_PATH, "check", "--json"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("cdp_running", result.stdout)

if __name__ == "__main__":
    unittest.main()
