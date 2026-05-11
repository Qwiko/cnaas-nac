# Cisco

Here are some example configuration for Cisco switches that work well with CNaaS-NAC.

## nas_identifier attribute

Enables nas_identifier in access-request and accounting-request packets.

```
radius-server attribute 32 include-in-access-req format %h
radius-server attribute 32 include-in-accounting-req format %h
```

## Accounting


```
aaa accounting update periodic 30 # In minutes
aaa accounting dot1x default start-stop group cnaas-nac
```

## CoA support

```
aaa server radius dynamic-author
 client 192.168.0.1
 server-key 7 XXXXX
 port 3799
 auth-type all
```

## Load balancing

```
aaa group server radius cnaas-nac
 load-balance method least-outstanding ignore-preferred-server
```
