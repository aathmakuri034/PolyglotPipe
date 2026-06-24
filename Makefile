.PHONY: lint typecheck test test-int security ci docker-up docker-down clean

lint:
	ruff check .
	ruff format --check .

typecheck:
	mypy polyglotpipe/

test:
	pytest tests/unit/ --cov=polyglotpipe --cov-report=term-missing --cov-fail-under=80

test-int:
	pytest tests/integration/

security:
	pip-audit

ci: lint typecheck test security

docker-up:
	docker compose up -d

docker-down:
	docker compose down

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov **/__pycache__
