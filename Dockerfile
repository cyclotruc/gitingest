# Stage 1: Install Python dependencies
FROM python:3.13-slim AS python-builder
WORKDIR /build

# System build tools
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Metadata and code that setuptools needs
COPY pyproject.toml .
COPY src/ ./src/

# Install runtime dependencies defined in pyproject.toml
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --timeout 1000 .


# Stage 2: Runtime image
FROM python:3.13-slim
LABEL org.opencontainers.image.source="https://github.com/cyclotruc/gitingest"

# Minimal runtime utilities
RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
RUN useradd -m -u 1000 appuser

# Copy Python site-packages and code
COPY --from=python-builder /usr/local/lib/python3.13/site-packages/ \
                           /usr/local/lib/python3.13/site-packages/
COPY src/ ./

# Set permissions
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
