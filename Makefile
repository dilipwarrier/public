.DEFAULT_GOAL := help

.PHONY: help test

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

test: ## Validate the public file paths in external_interfaces.json
	@echo "Validating external file interfaces..."
	@python3 tests/test_external_interfaces.py
