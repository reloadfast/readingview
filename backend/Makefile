.PHONY: lint type-check test security ci

lint:
	ruff check . --fix
	ruff format .

type-check:
	mypy app

test:
	pytest

security:
	bandit -r app -c pyproject.toml

ci: lint type-check security test
