# Endpoints

All radius users handled in CNaaS-NAC will be saved to a database as an Endpoint.

## State

An endpoint can be in four different states.

- Discovered

A rejected MAB endpoint that is first seen on the network.

- Rejected

A rejected endpoint. Usually by not matching any policy.

- Pending

A MAB endpoint that have been manually added or changed via the api and is waiting on the next authentication.

- Authorized

An endpoint that is authorized.


## Endpoint group

A MAB endpoint can be part of an endpoint group to easier match multiple different mac addresses in a policy.

Place endpoints to groups by setting the group_id field.

Policy example matching on a group_id.

```json
{
  "conditions": [
    {
        "attribute": "group_id",
        "operator": "==",
        "value": 1 # group_id
    }
  ],
}
```