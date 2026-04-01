# Development

## Prerequisites
 - Install [docker and docker compose](https://www.docker.com/get-started/)
 - Install [uv](https://docs.astral.sh/uv/getting-started/installation/)

## Run locally

```bash
# Start postgres db
docker compose -f docker/docker-compose.dev.yml up -d nac_postgres

# Run external api
uv run fastapi dev src/cnaas_nac/api_external/main.py 

# Run internal api
uv run fastapi dev src/cnaas_nac/api_internal/main.py 
```

## Run within docker
```bash
# Start postgres db
docker compose -f docker/docker-compose.dev.yml up -d
```