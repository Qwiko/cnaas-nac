FROM python:3.14.3-slim-trixie

LABEL org.opencontainers.image.vendor="SUNET"
LABEL org.opencontainers.image.source="https://github.com/SUNET/cnaas-nac"
LABEL org.opencontainers.image.description="CNaaS NAC radmin sidecar"

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONPATH="/app/src"
# Disable development dependencies
ENV UV_NO_DEV=1

# Install radmin dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    freeradius \
    && rm -rf /var/lib/apt/lists/*

# Copy uv from astral
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml .
COPY uv.lock .
RUN uv pip install --system -r pyproject.toml

# Create an unprivileged user for runtime
RUN addgroup --system -gid 1001 cnaas && \
    adduser --system -uid 1001 --ingroup cnaas --home /app --shell /bin/bash cnaas

# Copy full source code
COPY src ./src

RUN chown -R cnaas:cnaas /app

ENV HOME=/app
USER cnaas

# Use the script to manage the arguments
ENTRYPOINT ["python", "-u", "-m", "cnaas_nac.tools.radmin"]