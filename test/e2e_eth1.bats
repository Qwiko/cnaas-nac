source test/shared.bash

@test "test eos-a1 eth1 is on vlan14" {
    run clab_ceos_exec eos-a1 "show interfaces ethernet 1 status" 
    [ "$status" -eq 0 ]
    echo $output | grep -qE "connected\s14\s"
}

@test "test eos-a1 eth1 supplicant state SUCCESS" {
    run clab_ceos_exec eos-a1 "show dot1x hosts interface ethernet 1 detail | inc Supplicant.state" 
    [ "$status" -eq 0 ]
    echo $output | grep -q "SUCCESS"
}

@test "test eos-a1 eth1 Filter-Id" {
    run clab_ceos_exec eos-a1 "show dot1x hosts interface ethernet 1 detail | inc Filter-Id" 
    [ "$status" -eq 0 ]
    echo $output | grep -q "Ethernet1-ACL"
}

@test "test alpine c1 with mac 02:43:ac:00:00:c1 should have been accepted and get vlan14" {
    run clab_exec alpine-c1 "ping -c 1 192.168.1.1" 
    [ "$status" -eq 0 ]
    echo $output
    echo $output | grep -q "1 packets received, 0% packet loss"
}

@test "test eos-a1 eth1 coa port bounce" {
    endpoint_id=$(api_request "GET" "endpoint?username=02:43:ac:00:00:c1" | jq -r '.[].id')

    api_request "DELETE" "endpoint/$endpoint_id"

    run clab_ceos_exec eos-a1 "show interface ethernet 1 status"

    # Port bounced and displays as N/A
    echo $output | grep -qE "connected\s+N\/A\s"
}

