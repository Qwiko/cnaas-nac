load shared.bash

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

@test "test eos-a1 eth1 Filter-Id == Ethernet1-ACL" {
    run clab_ceos_exec eos-a1 "show dot1x hosts interface ethernet 1 detail | inc Filter-Id" 
    [ "$status" -eq 0 ]
    echo $output | grep -q "Ethernet1-ACL"
}

@test "test alpine-c1 IPv4 can ping default gateway" {
    run clab_exec alpine-c1 "ping -c 1 192.168.1.1" 
    [ "$status" -eq 0 ]
    echo $output | grep -q "1 packets received, 0% packet loss"
}

@test "test alpine-c1 IPv4 can ssh to eos-a1" {
    run clab_exec alpine-c1 "nc -zv 192.168.1.1 22" 
    [ "$status" -eq 0 ]
    echo $output | grep -q "open"
}

@test "test alpine-c1 IPv6 can ping default gateway" {
    run clab_exec alpine-c1 "ping6 -c 1 fd00:192:168:1::1" 
    [ "$status" -eq 0 ]
    echo $output | grep -q "1 packets received, 0% packet loss"
}

@test "test alpine-c1 IPv6 can ssh to eos-a1" {
    run clab_exec alpine-c1 "nc -zv fd00:192:168:1::1 22" 
    [ "$status" -eq 0 ]
    echo $output | grep -q "open"
}

@test "test eos-a1 eth1 matched IPv4 ACL" {
    run clab_ceos_exec eos-a1 "show ip access-lists Ethernet1-ACL | include match" 
    [ "$status" -eq 0 ]
    echo $output | grep -q "permit icmp"
    echo $output | grep -q "permit tcp"
}

@test "test eos-a1 eth1 matched IPv6 ACL" {
    run clab_ceos_exec eos-a1 "show ipv6 access-lists Ethernet1-ACL | include match" 
    [ "$status" -eq 0 ]
    echo $output | grep -q "permit icmpv6"
    echo $output | grep -q "permit tcp"
}

@test "test eos-a1 eth1 coa port bounce" {
    endpoint_id=$(api_request "GET" "endpoint?username=02:43:ac:00:00:c1" | jq -r '.[].id')

    [ "$endpoint_id" != "null" ]

    # Delete issues a CoA that causes the port to bounce
    api_request "DELETE" "endpoint/$endpoint_id"

    run clab_ceos_exec eos-a1 "show interface ethernet 1 status"

    # Port bounced and displays as N/A
    echo $output | grep -qE "connected\s+N\/A\s"
}
