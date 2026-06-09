# Testing

## Prerequisites
Install [development prerequisites](index.md)


## Pytest

```bash
# Start postgres db.
docker compose -f docker/docker-compose.dev.yml up -d nac_postgres

# Run tests locally
POSTGRES_SERVER=127.0.0.1 uv run --group dev pytest
```

## End to end tests

### Prerequisites

- Install [Bats](https://bats-core.readthedocs.io/en/stable/index.html).
- Install docker & docker compose.
- Install [containerlab](https://containerlab.dev/).
- Add [Arista cEOS image](https://containerlab.dev/manual/kinds/ceos/).


### Run in automatic mode

```bash
# Be in root folder of this repo.
# Need sudo access
bats test
```

### Run in manual mode

```bash
# Start docker dev compose
docker compose -f docker/docker-compose.dev.yml up --build -d

# Start containerlab
cd test
sudo containerlab deploy

# or run a specific cEOS version with:
sudo ARISTA_VERSION=4.35.4M containerlab deploy 

cd ..
# Run bats
MANUAL_TEST=1 bats test
```