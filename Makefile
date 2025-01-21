.PHONY: install-uv .clean test test-mutation docs-build docs-serve

.install-uv:
	@echo "---- 👷 Installing build dependencies ----"
	uv -V || pip install uv
	touch .install-uv

install-uv: .install-uv

.init: .install-uv
	@echo "---- 📦 Building package ----"
	rm -rf .venv
	uv sync --all-extras --dev
	git init .
	uv run pre-commit install --install-hooks
	touch .init

.clean:
	rm -rf .init .pytest_cache
	uv -V || rm -rf .install-uv

init: .clean .init
	@echo ---- 🔧 Re-initialized project ----

lint: .init
	uv run pre-commit run --all-files

test: .init
	@echo ---- ⏳ Running tests ----
	@(uv run coverage run -m pytest tests/ && echo "---- ✅ Tests passed ----" && exit 0 || echo "---- ❌ Tests failed ----" && exit 1)
	@(uv run coverage report)
	@(uv run coverage html)
