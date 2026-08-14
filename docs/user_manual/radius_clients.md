# Radius Clients

A RADIUS client can be dynamically created via the API and FreeRadius will use the database to setup the radius client dynamically during runtime.

Read more about this feature <a href="https://www.freeradius.org/documentation/freeradius-server/4.0.0/reference/raddb/sites-available/dynamic-clients.html" target="_blank">here</a>.

## Fields

The API uses the following fields for radius clients:

- `name` — Unique client name.
- `network` — Client source network in CIDR notation.
- `secret` — Shared secret used by the RADIUS client.
- `description` — Optional text description.
- `server` — FreeRADIUS site to use, typically `default` or `external`.
- `coa_enabled` — Whether Change of Authorization is enabled.
- `coa_port` — The COA port, default `3799`.
- `coa_secret` — Optional COA shared secret.

It is recommended to keep the network as small as possible for security reasons.

## Server sites

Use the `server` field to control which FreeRADIUS site the client is exposed through.

Read more about sites [here](index.md).

## Dynamic behavior

When a client is updated or deleted, CNaaS-NAC can clear the existing dynamic client state in FreeRADIUS.

- Updating a client's `secret` triggers a clear event so the new secret is applied.
- Deleting a client also clears the dynamic client definition from FreeRADIUS.

## Examples

Create a new dynamic RADIUS client using the external API:

```json
{
  "name": "BranchOffice1",
  "network": "10.10.10.0/24",
  "secret": "supersecret",
  "description": "Branch office RADIUS clients",
  "server": "default",
  "coa_enabled": true,
  "coa_port": 3799,
  "coa_secret": "coasecret" # Optional, will use secret if not set.
}
```

```json
{
  "name": "RemoteClient",
  "network": "123.4.5.6/32",
  "secret": "supersecret",
  "description": "Remote client that only need to validate EAP",
  "server": "external",
}
```
