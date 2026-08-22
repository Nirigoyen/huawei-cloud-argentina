.PHONY: up down logs rebuild seed clean

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

rebuild:
	docker compose up -d --build --force-recreate

seed:
	docker exec -i chatbi-postgres psql -U workshop -d scenario < docker/02-load-scenario.sql

clean:
	docker compose down -v
