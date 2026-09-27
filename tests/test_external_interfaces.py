#!/usr/bin/env python3
"""Validates the external_interfaces.json contract."""

import json
import os
import sys

CONTRACT_FILE = "external_interfaces.json"


def _validate_route(
    contract: dict[str, object], list_title: str, route: object
) -> int:
    """Validate one Google Tasks destination route."""
    if not isinstance(route, dict):
        print(f"Invalid Google Tasks route for '{list_title}': expected an object.")
        return 1

    route_type = route.get("type")
    if route_type in ("org", "csv"):
        contract_key = route.get("contract_key")
        if not isinstance(contract_key, str) or "." not in contract_key:
            print(f"Invalid path key for Google Tasks list '{list_title}'.")
            return 1

        domain, name = contract_key.split(".", 1)
        interfaces = contract.get(domain)
        relative_path = interfaces.get(name) if isinstance(interfaces, dict) else None
        if not isinstance(relative_path, str):
            print(
                f"Broken route: google_tasks.{list_title} references "
                f"unknown contract key '{contract_key}'."
            )
            return 1
        if not os.path.exists(relative_path):
            print(
                f"Broken route: google_tasks.{list_title} -> "
                f"'{relative_path}' does not exist."
            )
            return 1
        return 0

    if route_type == "jira":
        required_fields = (
            "command",
            "read_command",
            "title_argument",
            "due_date_argument",
            "project",
        )
        missing_fields = [
            field
            for field in required_fields
            if not isinstance(route.get(field), str) or not route[field].strip()
        ]
        if missing_fields:
            print(
                f"Invalid Jira route for '{list_title}': missing or empty "
                f"{', '.join(missing_fields)}."
            )
            return 1
        return 0

    print(f"Invalid route type for Google Tasks list '{list_title}': {route_type!r}.")
    return 1


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
        if not isinstance(interfaces, dict):
            print(f"Invalid contract domain '{domain}': expected an object.")
            errors += 1
            continue

        if domain == "google_tasks":
            for list_title, route in interfaces.items():
                errors += _validate_route(contract, list_title, route)
            continue

        for name, relative_path in interfaces.items():
            if not isinstance(relative_path, str):
                print(f"Invalid contract path for {domain}.{name}: expected a string.")
                errors += 1
                continue
            if not os.path.exists(relative_path):
                print(f"Broken contract: {domain}.{name} -> '{relative_path}' does not exist.")
                errors += 1

    if errors > 0:
        print(f"\nContract validation failed! {errors} missing file(s).")
        sys.exit(1)

    print("Contract validation passed. All mapped files and routes are valid.")

if __name__ == "__main__":
    main()
