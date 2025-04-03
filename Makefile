# Variables
DOCKER_COMPOSE := docker-compose -f docker-compose.yml
DOCKER_COMPOSE_PROD := docker-compose -f docker-compose.yml -f docker-compose.prod.yml
APP_NAME := document-ai
VERSION := $(shell git rev-parse --short HEAD)

.PHONY: help build up down logs test migrate clean

help:  ## Mostrar ayuda
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build:  ## Construir imágenes
	$(DOCKER_COMPOSE) build

up:  ## Iniciar entorno
	$(DOCKER_COMPOSE) up -d

down:  ## Detener entorno
	$(DOCKER_COMPOSE) down

logs:  ## Ver logs
	$(DOCKER_COMPOSE) logs -f

test:  ## Ejecutar tests
	$(DOCKER_COMPOSE) run --rm app pytest -v

migrate:  ## Ejecutar migraciones
	$(DOCKER_COMPOSE) run --rm migrator

prod-up:  ## Iniciar producción
	$(DOCKER_COMPOSE_PROD) up -d --scale app=3

prod-down:  ## Detener producción
	$(DOCKER_COMPOSE_PROD) down

clean:  ## Limpiar contenedores y volúmenes
	$(DOCKER_COMPOSE) down -v --remove-orphans

db-shell:  ## Acceder a la DB
	$(DOCKER_COMPOSE) exec db mysql -u$$(shell $(DOCKER_COMPOSE) exec db printenv MYSQL_USER) -p$$(shell $(DOCKER_COMPOSE) exec db printenv MYSQL_PASSWORD) $$(shell $(DOCKER_COMPOSE) exec db printenv MYSQL_DATABASE)