# Variables configurables
DOCKER_REGISTRY ?= your-docker-registry  # Ej: ghcr.io/tu-usuario
APP_NAME ?= document-ai
TAG ?= $(shell git rev-parse --short HEAD)
K8S_NAMESPACE ?= document-ai

.PHONY: help build push deploy k8s-apply k8s-delete

help:  ## Muestra esta ayuda
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build:  ## Construye la imagen Docker
	docker build -t $(DOCKER_REGISTRY)/$(APP_NAME):$(TAG) .

push: build  ## Sube la imagen al registro
	docker push $(DOCKER_REGISTRY)/$(APP_NAME):$(TAG)

deploy: push k8s-apply  ## Despliega en Kubernetes (build + push + apply)

k8s-apply:  ## Aplica los manifiestos Kubernetes
	@echo "Aplicando configuraciones en namespace $(K8S_NAMESPACE)"
	kubectl create namespace $(K8S_NAMESPACE) 2>/dev/null || true
	kubectl apply -f k8s/ --namespace $(K8S_NAMESPACE)

k8s-delete:  ## Elimina los recursos Kubernetes
	kubectl delete -f k8s/ --namespace $(K8S_NAMESPACE)

local-up:  ## Levanta el entorno local con Docker Compose
	docker-compose -f docker-compose.yml up -d

local-down:  ## Detiene el entorno local
	docker-compose -f docker-compose.yml down