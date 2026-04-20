# Development

## Prerequisites
 - Install [docker and docker compose](https://www.docker.com/get-started/)
 - Install [uv](https://docs.astral.sh/uv/getting-started/installation/)

## Generate jwt access_token

```bash
uv run python -c '
from datetime import datetime, timedelta, timezone

from cnaas_nac.core.security import _create_jwt_token

token = _create_jwt_token({
    "username": "test_user",
    "rbac_groups": [],
    "endpoint_group_ids": [],
    "is_admin": True,
    "permissions": {},
    "exp": datetime.now(timezone.utc) + timedelta(minutes=60)}
)
print(token)
'
```

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
!!! warning "WIP"
    Need to be updated
```bash
docker compose -f docker/docker-compose.dev.yml up -d
```

## Developing documentation
```bash
uv run --group docs mkdocs serve
```