FROM python:3.14.3-slim-trixie

LABEL org.opencontainers.image.vendor="SUNET"
LABEL org.opencontainers.image.source="https://github.com/SUNET/cnaas-nac"
LABEL org.opencontainers.image.description="CNaaS NAC"

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONPATH="/app/src"
# App environment
ENV ENVIRONMENT="production"

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY alembic.ini .
COPY alembic ./alembic

# Copy full source code
COPY src .

COPY docker/api/docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Expose HTTPS
EXPOSE 8000

# Use the script to manage the arguments
ENTRYPOINT ["docker-entrypoint.sh"]

# Default to external if no argument is passed
CMD ["external"]