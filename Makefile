.PHONY: doctor setup run test docker docker-down docker-reset seed

doctor:
	./scripts/doctor.sh

setup:
	./scripts/bootstrap-local.sh

run:
	./scripts/run-local.sh

test:
	./scripts/test-local.sh

seed:
	cd backend && . .venv/bin/activate && DB_ENGINE=sqlite USE_CELERY=0 python manage.py seed_demo --sessions 120

docker:
	@test -f .env || cp .env.example .env
	docker compose up --build

docker-down:
	docker compose down

docker-reset:
	docker compose down -v
