# RealtyRecall local development.
# `make up` is the one-command bring-up (see scripts/up.sh).

.PHONY: up down logs seed smoke

up:
	@bash scripts/up.sh

down:
	docker compose down

logs:
	docker compose logs -f

seed:
	docker compose run --rm seed

smoke:
	@bash scripts/smoke.sh
