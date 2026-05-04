#!/usr/bin/env python3
"""Validates the external_interfaces.json contract."""

import json
import os
import sys

CONTRACT_FILE = "external_interfaces.json"

def main() -> None:
    if not os.path.exists(CONTRACT_FILE):
        print(f"Error: Contract file '{CONTRACT_FILE}' is missing!")
        sys.exit(1)

    with open(CONTRACT_FILE, "r", encoding="utf-8") as f:
        try:
            contract = json.load(f)
        except json.JSONDecodeError as err:
            print(f"Error: '{CONTRACT_FILE}' contains invalid JSON. {err}")
            sys.exit(1)

    errors = 0
    for domain, interfaces in contract.items():
        for name, relative_path in interfaces.items():
            if not os.path.exists(relative_path):
                print(f"Broken contract: {domain}.{name} -> '{relative_path}' does not exist.")
                errors += 1

    if errors > 0:
        print(f"\nContract validation failed! {errors} missing file(s).")
        sys.exit(1)

    print("Contract validation passed. All mapped files exist.")

if __name__ == "__main__":
    main()
