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

@test "test eos-a1 eth1 EAP authorization" {
    # Reset any previous runs
    run clab_exec alpine-c1 "rm /var/run/wpa_supplicant/eth1"
    run clab_exec alpine-c1 "pgrep wpa_supplicant | xargs kill"
    # Start wpa_supplicant on alpine-c1 to trigger EAP authentication
    run clab_exec alpine-c1 "wpa_supplicant -Dwired -i eth1 -c /tmp/wpa_supplicant.conf -B"

    # Sleep for a few seconds to allow the EAP authentication to complete
    sleep 5

    # Check that the switch sees the EAP client
    run clab_ceos_exec eos-a1 "show dot1x hosts interface Ethernet 1 detail | include Supplicant:" 
    [ "$status" -eq 0 ]
    echo $output | grep -q "user@example.org"

    # Revert wpa_supplicant on alpine-c1 to avoid affecting other tests
    run clab_exec alpine-c1 "rm /var/run/wpa_supplicant/eth1"
    run clab_exec alpine-c1 "pgrep wpa_supplicant | xargs kill"
}

@test "test eos-a1 eth1 coa port bounce" {
    # Depends on the previous EAP test
    # Get CoA requests before
    run clab_ceos_exec eos-a1 "show radius | grep CoA.requests | grep -oP \"[0-9]+\""

    pre_count=$(echo "$output" | jq ".stdout")

    endpoint_id=$(api_request "GET" "endpoint?username=user%40example.org" | jq -r '.[].id')

    [ "$endpoint_id" != "null" ]

    # Delete issues a CoA that causes the port to bounce
    api_request "DELETE" "endpoint/$endpoint_id"

    # sleep 1

    run clab_ceos_exec eos-a1 "show radius | grep CoA.requests | grep -oP \"[0-9]+\""

    after_count=$(echo "$output" | jq ".stdout")

    [ "$after_count" -gt "$pre_count" ]
}