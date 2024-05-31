.PHONY: install-poetry .clean test test-mutation docs-build docs-serve

GIT_SHA = $(shell git rev-parse --short HEAD)
PACKAGE_VERSION = $(shell poetry version -s | cut -d+ -f1)

.install-poetry:
	@echo "---- 👷 Installing build dependencies ----"
	deactivate > /dev/null 2>&1 || true
	poetry -V || pipx install poetry
	touch .install-poetry

install-poetry: .install-poetry

.init: .install-poetry
	@echo "---- 📦 Building package ----"
	rm -rf .venv
	poetry install
	git init .
	poetry run pre-commit install --install-hooks
	touch .init

.clean:
	rm -rf .init .pytest_cache
	poetry -V || rm -rf .install-poetry

init: .clean .init
	@echo ---- 🔧 Re-initialized project ----

lint: .init
	pre-commit run --all-files

test: .init
	@echo ---- ⏳ Running tests ----
	@(poetry run coverage run -m pytest tests/ && echo "---- ✅ Tests passed ----" && exit 0 || echo "---- ❌ Tests failed ----" && exit 1)
	@(poetry run coverage report)
	@(poetry run coverage html)
