install:
	poetry install --with dev

test:
	poetry run python -m pytest -vv tests

type:
	poetry run mypy fastevent tests
