source test/shared.bash

@test "test eos-a1 eth2 mac is discovered" {
    run api_request "GET" "endpoint?q=02:43:ac:00:00:c2" \| jq -r '.[0].state'

    # [ "$status" -eq 0 ]
    [ "${lines[0]}" = "discovered" ]
    echo "$output" | grep -q "discovered"
}

