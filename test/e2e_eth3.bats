#!/usr/bin/env bats

load shared.bash

@test "test eos-a1 eth3 mac is rejected by a policy" {
    run bats_pipe api_request "GET" "endpoint?q=02:43:ac:00:00:c3" \| jq -r '.[0].state'

    [ "$status" -eq 0 ]
    [ "${lines[0]}" = "rejected" ]
}

