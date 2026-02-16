function docker_radtest() {
    # $1 is a mac-address
    docker compose -f docker/docker-compose.dev.yml exec -it nac_radius radtest -4 -t pap $1 $1 localhost:1812 0 testing123
}

@test "test Access-Reject: 00:00:00:00:00:00" {
    run docker_radtest "00:00:00:00:00:00"
    [ "$status" -eq 1 ]
    echo $output | grep -q "Expected Access-Accept got Access-Reject"
}

