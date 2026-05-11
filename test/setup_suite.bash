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
  "network": "0.0.0.0/0",
  "description": "",
  "server": "default",
  "secret": "testing123",
  "coa_enabled": true
}
EOF
)"
}

function setup_policy_eth1() {
    log "Setting up API policy..."
    api_request "GET" "policy?name=alpine-c1%20to%20vlan14" | grep -q "alpine-c1 to vlan14" && \
    log "Policy already exists, skipping creation." && \
    return 0

    api_request "POST" "policy" "$(cat <<EOF
{
  "name": "alpine-c1 to vlan14",
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

function setup_policy_eth3() {
    log "Setting up API policy..."
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

function start_environment() {
    log "Setting up Docker containers..."
    run docker compose -f docker/docker-compose.dev.yml up --force-recreate --build -d &
    log "Setting up containerlab environment..."
    run sudo -n containerlab -t test/e2e.clab.yml deploy --reconfigure &
    log "Containerlab is being deployed."
}

function setup_api() {
    setup_radius_client
    setup_policy_eth1
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
    if ! sudo -n containerlab 2>/dev/null; then
        log "ERROR: This test suite requires passwordless containerlab privileges!"
        log "Please configure sudoers or run the suite as root."
        return 1 # Abort the test suite cleanly
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
}

function teardown_suite() {
    if [ -n "$MANUAL_TEST" ]; then
        log "Manual test mode enabled, skipping cleanup."
        return 0
    fi
    log "Tearing down the environment..."
    run docker compose -f docker/docker-compose.dev.yml down -v
    run sudo -n containerlab -t test/e2e.clab.yml destroy
}