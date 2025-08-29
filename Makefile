install:
	poetry install --with dev

test:
	poetry run python -m pytest -vv tests -m '' --cov=fastevent --cov-report=term-missing --cov-fail-under=95

type:
	poetry run mypy fastevent tests
