.PHONY: setup index test portable portable-inputs lint typecheck check report manuscript dashboard skills-check
PORTABLE_INPUTS ?= .rikishi/portable-inputs/default
setup:
	uv sync --locked
	uv run rikishi bootstrap
index:
	uv run rikishi index
test: portable-inputs
	RIKISHI_PORTABLE_INPUTS="$(abspath $(PORTABLE_INPUTS))" uv run pytest --cov=rikishi --cov-report=term-missing --cov-report=json:output/coverage.json --junitxml=output/tests.xml
	uv run python scripts/check_coverage.py --output output/coverage-gates.json
portable-inputs:
	mkdir -p "$(dir $(PORTABLE_INPUTS))"
	uv run --locked --no-sync python scripts/prepare_portable_inputs.py --output "$(PORTABLE_INPUTS)" --reuse
portable: skills-check portable-inputs
	RIKISHI_PORTABLE_INPUTS="$(abspath $(PORTABLE_INPUTS))" uv run pytest -m 'not integration'
skills-check:
	uv run python scripts/sync_skills.py
lint:
	uv run ruff check src tests scripts typings
typecheck:
	uv run basedpyright
check: skills-check lint typecheck test
	uv build
report:
	uv run rikishi report
manuscript:
	uv run python scripts/render_manuscript.py
dashboard:
	uv run rikishi dashboard
