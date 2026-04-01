# Testing

## Prerequisites
Install [development prerequisites](development.md)


## Pytest

```bash
# Start postgres db.
docker compose -f docker/docker-compose.dev.yml up -d nac_postgres

# Run tests locally
POSTGRES_SERVER=127.0.0.1 uv run --group dev pytest
```

## End to end tests
!!! warning "WIP"
    Work in progress