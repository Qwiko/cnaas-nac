#!/bin/bash

function setup_suite() {
    run docker compose -f docker/docker-compose.dev.yml up --force-recreate --build -d --remove-orphans
    run docker compose -f docker/docker-compose.dev.yml exec -it nac_radius sh -c 'apk update && apk add freeradius-utils'
    run sudo containerlab deploy
}

# function teardown_suite() {
#     run docker compose -f docker/docker-compose.dev.yml down
#     run sudo containerlab destroy
# }