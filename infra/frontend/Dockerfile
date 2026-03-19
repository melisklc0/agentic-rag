# ==========================================
# Builder Stage
# ==========================================
FROM python:3.13-slim AS builder

# Keep runtime behavior predictable and logs visible in container environments.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1

WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency metadata (assuming frontend will have its own or share project's)
# If frontend uses the same pyproject.toml:
COPY pyproject.toml uv.lock ./

# Install dependencies including streamlit
RUN --mount=type=cache,target=/root/.cache \
    uv sync --locked --no-dev --no-install-project

# ==========================================
# Runtime Stage
# ==========================================
FROM python:3.13-slim AS runtime

WORKDIR /app

# Runtime uses a non-root user.
RUN useradd --create-home --shell /usr/sbin/nologin app

# Copy dependencies and application code
COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --chown=app:app src/services/frontend ./src/services/frontend

# Ensure runtime entrypoints stay executable
RUN find /app/.venv/bin -type f -exec chmod 755 {} +

USER app
EXPOSE 8501

# Streamlit specific healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD /app/.venv/bin/python -m streamlit help || exit 1

# Run Streamlit
CMD ["/app/.venv/bin/python", "-m", "streamlit", "run", "src/services/frontend/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
