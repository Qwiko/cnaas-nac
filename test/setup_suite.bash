#!/bin/bash

source test/shared.bash

function setup_radius_client() {
    log "Setting up radius client..."
    api_request "GET" "radius_client?name=clab" | grep -q "clab" && \
    log "Radius client already exists, skipping creation." && \
    return 0

    api_request "POST" "radius_client" "$(cat <<EOF
{
  "name": "clab",
  "network": "10.5.0.0/24",
  "description": "",
  "server": "default",
  "secret": "testing123",
  "coa_enabled": true
}
EOF
)"
}

function setup_policy_eth1_mab() {
    log "Setting up API policy for eth1 MAB..."
    api_request "GET" "policy?name=alpine-c1%20to%20vlan14%20MAB" | grep -q "alpine-c1 to vlan14 MAB" && \
    log "Policy already exists, skipping creation." && \
    return 0

    api_request "POST" "policy" "$(cat <<EOF
{
  "name": "alpine-c1 to vlan14 MAB",
  "match_logic": "AND",
  "client_type": "MAB",
  "port_type": "Ethernet",
  "enabled": true,
  "conditions": [
    {
        "attribute": "calling_station_id",
        "operator": "==",
        "value": "02:43:ac:00:00:c1"
    }
  ],
  "replies": [
    {
        "attribute": "Tunnel-Medium-Type",
        "value": "IEEE-802"
    },
    {
        "attribute": "Tunnel-Type",
        "value": "VLAN"
    },
    {
        "attribute": "Tunnel-Private-Group-Id",
        "value": "14"
    },
    {
        "attribute": "Filter-Id",
        "value": "Ethernet1-ACL"
    }
  ]
}
EOF
)"
}


function setup_policy_eth1_eap() {
    log "Setting up API policy for eth1 EAP..."
    api_request "GET" "policy?name=alpine-c1%20to%20vlan14%20EAP" | grep -q "alpine-c1 to vlan14 EAP" && \
    log "Policy already exists, skipping creation." && \
    return 0

    api_request "POST" "policy" "$(cat <<EOF
{
  "name": "alpine-c1 to vlan14 EAP",
  "match_logic": "AND",
  "client_type": "EAP",
  "port_type": "Ethernet",
  "enabled": true,
  "conditions": [
    {
        "attribute": "username",
        "operator": "==",
        "value": "user@example.org"
    }
  ],
  "replies": [
    {
        "attribute": "Tunnel-Medium-Type",
        "value": "IEEE-802"
    },
    {
        "attribute": "Tunnel-Type",
        "value": "VLAN"
    },
    {
        "attribute": "Tunnel-Private-Group-Id",
        "value": "14"
    },
    {
        "attribute": "Filter-Id",
        "value": "Ethernet1-ACL"
    }
  ]
}
EOF
)"
}

function setup_policy_eth3() {
    log "Setting up API policy for eth3..."
    api_request "GET" "policy?name=alpine-c3%20reject" | grep -q "alpine-c3 reject" && \
    log "Policy already exists, skipping creation." && \
    return 0

    api_request "POST" "policy" "$(cat <<EOF
{
  "name": "alpine-c3 reject",
  "priority": 90,
  "match_logic": "AND",
  "client_type": "MAB",
  "port_type": "Ethernet",
  "enabled": true,
  "conditions": [
    {
        "attribute": "calling_station_id",
        "operator": "==",
        "value": "02:43:ac:00:00:c3"
    }
  ],
  "replies": [
    {
        "attribute": "Auth-Type",
        "value": "Reject"
    }
  ]
}
EOF
)"
}


function bootstrap_radius_ca() {
    log "Bootstrapping RADIUS CA..."
    docker compose -f docker/docker-compose.dev.yml exec -u root nac_radius sh -c \
        "apk add make openssl freeradius && \ 
        cd /etc/raddb/certs && \
        make destroycerts && make all \
        && chown -R radius:radius /etc/raddb/certs"
    log "Restarting nac_radius container to apply new certs..."
    docker compose -f docker/docker-compose.dev.yml restart nac_radius

    log "Waiting for nac_radius container to be ready..."
    local max_wait=60  # 1 minute in seconds
    local elapsed=0

    until docker compose -f docker/docker-compose.dev.yml exec nac_radius sh -c \
        "radmin -e 'show version'" &>/dev/null; do
        if (( elapsed >= max_wait )); then
            log "ERROR: nac_radius container failed to be ready within ${max_wait}s"
            return 1
        fi
        if (( elapsed % 5 == 0 )); then
            log -n "."
        fi
        
        sleep 1
        (( ++elapsed ))
    done
    log "" && log "nac_radius container is ready."

    log "Copying RADIUS CA and client certs to alpine-c1..."
    docker compose -f docker/docker-compose.dev.yml cp nac_radius:/etc/raddb/certs/ca.pem /tmp
    docker compose -f docker/docker-compose.dev.yml cp nac_radius:/etc/raddb/certs/client.pem /tmp
    docker compose -f docker/docker-compose.dev.yml cp nac_radius:/etc/raddb/certs/client.key /tmp

    docker cp /tmp/ca.pem clab-cnaas-nac-e2e-alpine-c1:/tmp
    docker cp /tmp/client.pem clab-cnaas-nac-e2e-alpine-c1:/tmp
    docker cp /tmp/client.key clab-cnaas-nac-e2e-alpine-c1:/tmp

    docker cp test/wpa_supplicant.conf clab-cnaas-nac-e2e-alpine-c1:/tmp

    docker exec clab-cnaas-nac-e2e-alpine-c1 sh -c "chown root:root /tmp/*"
}



function start_environment() {
    local image_version=${ARISTA_VERSION:=4.35.4M}

    if ! docker image inspect ceos:$image_version > /dev/null 2>&1; then
        log "No ceos image found! (ceos:$image_version is missing)"
        return 1
    fi

    log "Setting up Docker containers..."
    docker compose -f docker/docker-compose.dev.yml up --force-recreate --build -d &>/dev/null &
    log "Setting up containerlab environment..."
    sudo ARISTA_VERSION=$image_version -n containerlab -t test/e2e.clab.yml deploy --reconfigure &>/dev/null &
    log "Containerlab is being deployed."
}

function setup_api() {
    setup_radius_client
    setup_policy_eth1_mab
    setup_policy_eth1_eap
    setup_policy_eth3
    log "API setup completed."
}

function wait_for_api() {
    log "Waiting for API to be ready..."
    local max_wait=60  # 1 minute in seconds
    local elapsed=0
    
    until api_request "GET" "health" | grep -q "up"; do
        if (( elapsed >= max_wait )); then
            log "ERROR: API failed to be ready within ${max_wait}s"
            return 1
        fi
        if (( elapsed % 5 == 0 )); then
            log -n "."
        fi
        
        sleep 1
        (( ++elapsed ))
    done
    log "" && log "API is ready."
}

function wait_for_containerlab() {
    log "Waiting for containerlab to be ready, this might take a while..."
    
    local max_wait=300  # 5 minutes in seconds
    local elapsed=0
    
    until clab_ceos_exec eos-a1 "show mac add | inc 0243.ac" 2>/dev/null | grep -q "STATIC"; do
        if (( elapsed >= max_wait )); then
            log "ERROR: Containerlab failed to be ready within ${max_wait}s"
            return 1
        fi
        if (( elapsed % 5 == 0 )); then
            log -n "."
        fi
        
        sleep 1
        (( ++elapsed ))
    done
    log "" && log "Containerlab is ready."
}

function setup_suite() {
    if ! sudo -n containerlab &>/dev/null; then
        log "ERROR: This test suite requires passwordless containerlab privileges!"
        log "Please configure sudoers or run the test suite as root."
        if [[ -n "${BATS_VERSION}" ]]; then
            return 1 # Abort the test suite cleanly
        else
            exit 1
        fi
    fi
    log "Sudo access confirmed. Setting up the environment..."

    if [ -n "$MANUAL_TEST" ]; then
        log "Manual test mode enabled, skipping creation of docker / containerlab."
    else
        start_environment
    fi
    wait_for_api
    setup_api
    wait_for_containerlab
    bootstrap_radius_ca
}

function teardown_suite() {
    if [ -n "$MANUAL_TEST" ]; then
        log "Manual test mode enabled, skipping cleanup."
        return 0
    fi
    log "Tearing down the environment..."
    docker compose -f docker/docker-compose.dev.yml down -v &>/dev/null || true
    sudo -n containerlab -t test/e2e.clab.yml destroy --cleanup &>/dev/null || true
}