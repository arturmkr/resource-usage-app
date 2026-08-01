FROM ghcr.io/astral-sh/uv:0.11.15 AS uv

FROM python:3.14-slim AS builder
COPY --from=uv /uv /uvx /bin/
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

FROM python:3.14-slim
RUN useradd --create-home --uid 10001 userhub
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY src ./src
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
USER userhub
EXPOSE 10700
CMD ["python", "-m", "src.app"]
