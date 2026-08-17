# SECUROXI AI Production Multi-Stage Hardened Dockerfile
# Stage 1: Build Dependencies
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Final Minimal Runtime Image
FROM python:3.12-slim AS runner

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root unprivileged runtime user
RUN groupadd -g 10001 securoxigroup && \
    useradd -u 10001 -g securoxigroup -m -s /bin/bash securoxiuser

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application source code
COPY --chown=securoxiuser:securoxigroup . /app

# Ensure runtime directories exist with appropriate permissions
RUN mkdir -p /app/scratch /app/tmp && \
    chown -R securoxiuser:securoxigroup /app

USER securoxiuser

ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV ENVIRONMENT=production

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/api/v1/health/liveness || exit 1

CMD ["uvicorn", "securoxi.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
