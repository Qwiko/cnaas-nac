#!/bin/bash


API_URL="http://localhost:8000/api/v2/"
API_TOKEN=$(uv run python -c '
from datetime import datetime, timedelta, timezone

from cnaas_nac.core.security import _create_jwt_token

token = _create_jwt_token({
    "username": "test_admin_user",
    "rbac_groups": [],
    "endpoint_group_ids": [],
    "is_admin": True,
    "permissions": {},
    "exp": datetime.now(timezone.utc) + timedelta(hours=8)}
)
print(token)
')

function log() {
    echo "$@" >&3
}

function api_request() {
    local method=$1
    local endpoint=$2
    local data=$3

    curl -s -X "$method" "$API_URL$endpoint" \
        -H "Authorization: Bearer $API_TOKEN" \
        -H "Content-Type: application/json" \
        -d "$data"
}

function clab_ceos_exec() {
    # $1 is the name of the containerlab ceos node, $2 is the command to execute
    sudo -n containerlab -t test/e2e.clab.yml exec --format json --label name=$1 --cmd "Cli -p 15 -c '$2'" | jq -r '.[].[]'
}

function clab_exec() {
    # $1 is the name of the containerlab node, $2 is the command to execute
    sudo -n containerlab -t test/e2e.clab.yml exec --format json --label name=$1 --cmd "$2" | jq -r '.[].[]'
}