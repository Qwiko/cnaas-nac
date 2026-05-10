# Arista

Here are some example configuration for Arista switches that work well with CNaaS-NAC.

## Enable nas_identifier

Enables nas_identifier in access-request packets.

```
radius-server attribute 32 include-in-access-req hostname
```

## Enable accounting

```
aaa accounting dot1x default start-stop group cnaas-nac
dot1x
   aaa accounting update interval 1800 seconds # In seconds
```

## Enable CoA support

```
dot1x dynamic-authorization
```

## Load balancing

```
dot1x
   aaa authentication load-balance round-robin
```
