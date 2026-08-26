#!/usr/bin/env python3
"""
Unit tests for Chrome Native Messaging Bridge
"""

import json
import os
import subprocess
import unittest

SCRIPT_DIR = os.path.dirname(__file__)
BRIDGE_SCRIPT = os.path.join(SCRIPT_DIR, ".agents", "skills", "chrome-monitor", "scripts", "extension_bridge.py")
NATIVE_HOST_SCRIPT = os.path.join(SCRIPT_DIR, ".agents", "skills", "chrome-monitor", "scripts", "native_host.py")
PYTHON_BIN = os.path.join(SCRIPT_DIR, ".venv", "bin", "python")
EXTENSION_DIR = os.path.join(SCRIPT_DIR, "extension")

class TestNativeMessagingBridge(unittest.TestCase):

    def test_extension_manifest(self):
        """Verify manifest.json contains nativeMessaging permission."""
        manifest_path = os.path.join(EXTENSION_DIR, "manifest.json")
        self.assertTrue(os.path.exists(manifest_path))
        with open(manifest_path, "r") as f:
            data = json.load(f)
        self.assertIn("nativeMessaging", data.get("permissions", []))

    def test_native_host_exists(self):
        """Verify native_host.py exists."""
        self.assertTrue(os.path.exists(NATIVE_HOST_SCRIPT))

    def test_bridge_cli_help(self):
        """Verify CLI help output."""
        result = subprocess.run(
            [PYTHON_BIN, BRIDGE_SCRIPT, "--help"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Antigravity Chrome Native Bridge CLI", result.stdout)

    def test_host_manifest_registered(self):
        """Verify host JSON was placed in Chrome NativeMessagingHosts directory."""
        host_json = os.path.expanduser("~/Library/Application Support/Google/Chrome/NativeMessagingHosts/com.antigravity.chrome_monitor.json")
        self.assertTrue(os.path.exists(host_json))

if __name__ == "__main__":
    unittest.main()
