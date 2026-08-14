# Arista

Here are some example configuration for Arista switches that work well with CNaaS-NAC.

## nas_identifier attribute

Enables nas_identifier in access-request packets.

```arista
radius-server attribute 32 include-in-access-req hostname
```

## Accounting

```arista
aaa accounting dot1x default start-stop group cnaas-nac
dot1x
   aaa accounting update interval 1800 seconds # In seconds
```

## CoA support

```arista
dot1x dynamic-authorization
```

## Load balancing

```arista
dot1x
   aaa authentication load-balance round-robin
```
