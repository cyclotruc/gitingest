# ---------- Stage 1:  Build CSS with Node -------------------------
FROM node:20-alpine AS css-builder
WORKDIR /frontend

# Copy only files that affect the CSS build to leverage Docker cache
COPY package*.json ./
RUN npm ci

# Tailwind source --> final CSS
#   (adjust the paths if you store Tailwind input elsewhere)
# Tailwind config
COPY tailwind.config.js ./
# Tailwind input file(s)
COPY src/static/css/ ./src/static/css/
# writes ./src/static/css/site.css
RUN npm run build:css


# ---------- Stage 2:  Install Python dependencies -----------------
FROM python:3.12-slim AS python-builder
WORKDIR /build

# System build tools first (so later layers are cached if unchanged)
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --timeout 1000 "."


# ---------- Stage 3:  Final runtime image -------------------------
FROM python:3.12-slim
LABEL org.opencontainers.image.source="https://github.com/cyclotruc/gitingest"

# Minimal runtime utilities
RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Create non-root user (uid 1000 == common default on Linux host)
RUN useradd -m -u 1000 appuser

# ── Copy Python site-packages & app code ───────────────────────────
COPY --from=python-builder /usr/local/lib/python3.12/site-packages/ \
                           /usr/local/lib/python3.12/site-packages/
COPY src/ ./

# ── Copy the freshly-built CSS ────────────────────────────────────
COPY --from=css-builder /frontend/src/static/css/site.css \
                        src/static/css/site.css

# Fix permissions
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
