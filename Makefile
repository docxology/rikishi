.PHONY: setup index test lint report manuscript dashboard
setup:
	uv sync --locked
	uv run rikishi bootstrap
index:
	uv run rikishi index
test:
	uv run pytest --cov=rikishi --cov-report=term-missing
lint:
	uv run ruff check src tests scripts
report:
	uv run rikishi report
manuscript:
	uv run python scripts/render_manuscript.py
dashboard:
	uv run rikishi dashboard
