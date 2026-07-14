#!/usr/bin/env bats

load shared.bash

@test "test eos-a1 eth1 is on vlan14" {
    run clab_ceos_exec eos-a1 "show interfaces Ethernet 1 status" 
    [ "$status" -eq 0 ]
    echo $output | grep -qE "connected\s14\s"
}

@test "test eos-a1 eth1 supplicant state SUCCESS" {
    run clab_ceos_exec eos-a1 "show dot1x hosts interface Ethernet 1 detail | inc Supplicant.state" 
    [ "$status" -eq 0 ]
    echo $output | grep -q "SUCCESS"
}

@test "test eos-a1 eth1 Filter-Id == Ethernet1-ACL" {
    run clab_ceos_exec eos-a1 "show dot1x hosts interface Ethernet 1 detail | inc Filter-Id" 
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

    run clab_ceos_exec eos-a1 "show interface Ethernet 1 status"

    # Port bounced and displays as N/A
    echo $output | grep -qE "connected\s+N\/A\s"
}

@test "test eos-a1 eth1 EAP authorization" {
    # Install wpa_supplicant on alpine-c1 and start it to trigger EAP authentication
    run clab_exec alpine-c1 "apk add wpa_supplicant"
    # Start wpa_supplicant on alpine-c1 to trigger EAP authentication
    run clab_exec alpine-c1 "wpa_supplicant -Dwired -i eth1 -c /tmp/wpa_supplicant.conf -B"

    # Sleep for a few seconds to allow the EAP authentication to complete
    sleep 3

    # Check that the switch sees the EAP client
    run clab_ceos_exec eos-a1 "show dot1x hosts interface Ethernet 1 detail | include Supplicant:" 
    [ "$status" -eq 0 ]
    echo $output | grep -q "user@example.org"

    # Revert wpa_supplicant on alpine-c1 to avoid affecting other tests
    run clab_exec alpine-c1 "rm /var/run/wpa_supplicant/eth1"
    run clab_exec alpine-c1 "pgrep wpa_supplicant | xargs kill"
    run clab_ceos_exec eos-a1 "clear dot1x host interface Ethernet 1" 
}