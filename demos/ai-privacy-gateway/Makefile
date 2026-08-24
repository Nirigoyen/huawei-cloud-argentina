.PHONY: up down logs rebuild clean

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

rebuild:
	docker compose up -d --build --force-recreate

clean:
	docker compose down -v --rmi all
