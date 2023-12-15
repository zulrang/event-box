test:
	poetry run pytest

lint:
	poetry run ruff src

type:
	poetry run mypy .

qa: lint type test
