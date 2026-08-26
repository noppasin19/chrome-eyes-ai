#!/usr/bin/env python3
"""
Register Chrome Native Messaging Host on macOS
Creates the JSON host manifest in ~/Library/Application Support/Google/Chrome/NativeMessagingHosts/
"""

import json
import os
import stat
import sys

HOST_NAME = "com.antigravity.chrome_monitor"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
NATIVE_HOST_PATH = os.path.join(SCRIPT_DIR, "native_host.py")

# Manifest destinations on macOS
TARGET_DIRS = [
    os.path.expanduser("~/Library/Application Support/Google/Chrome/NativeMessagingHosts"),
    os.path.expanduser("~/Library/Application Support/Chromium/NativeMessagingHosts")
]

def register():
    # Make native_host.py executable
    os.chmod(NATIVE_HOST_PATH, 0o755)

    manifest_data = {
        "name": HOST_NAME,
        "description": "Antigravity Chrome Monitor Native Host",
        "path": NATIVE_HOST_PATH,
        "type": "stdio",
        "allowed_origins": [
            "chrome-extension://njdmlnpciddjgcohnfgjkcbjnhkieehn/"
        ]
    }

    for target_dir in TARGET_DIRS:
        try:
            os.makedirs(target_dir, exist_ok=True)
            target_json = os.path.join(target_dir, f"{HOST_NAME}.json")
            with open(target_json, "w") as f:
                json.dump(manifest_data, f, indent=2)
            os.chmod(target_json, 0o644)
            print(f"[SUCCESS] Registered Native Host at: {target_json}")
        except Exception as e:
            print(f"[WARN] Could not write to {target_dir}: {e}")

if __name__ == "__main__":
    register()
