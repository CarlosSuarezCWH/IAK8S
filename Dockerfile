# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app
ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim as runtime

WORKDIR /app
ENV PATH=/root/.local/bin:$PATH \
    PYTHONPATH=/app

# Dependencias de runtime
RUN apt-get update && \
    apt-get install -y --no-install-recommends libmariadb3 libpq5 && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /root/.local
COPY . .

# Configuración de usuario seguro
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser appuser && \
    chown -R appuser:appuser /app

USER appuser

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]