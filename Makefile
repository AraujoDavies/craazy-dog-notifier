.PHONY: run
run:
	poetry run python code/main.py

.PHONY: dev
dev:
	poetry run ipython -i code/perro_loko.py

.PHONY: db
db:
	poetry run python code/db.py

.PHONY: requirements
requirements:
	poetry export -o requirements.txt --without-hashes

.PHONY: down
down:
	docker compose down

.PHONY: up
up:
	@make down
	docker compose up -d

logs:
	docker compose logs --follow