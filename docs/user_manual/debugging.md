# Debugging

NAC includes a live debugging feature that can stream FreeRADIUS logs directly to the frontend.

To start a session, create a debug filter that defines the exact packet attributes to match. All fields in the filter are combined with a logical AND, so only packets matching every condition will be streamed.

Fields available for debug filtering:

- Username
- NAS Identifier
- NAS Port ID
- Calling Station ID
- Called Station ID
- NAS IP Address
- Realm

Example filter:

```json
{
  "username": "user@example.org",
  "nas_identifier": "eos-a1"
}
```

This filter matches only RADIUS packets where both:

- `username` equals `user@example.org`
- `nas_identifier` equals `eos-a1`

The limit is currently set to display a maximum of 1000 lines in the frontend.
If you need more lines the debug log file can be viewed directly at `/var/log/radius/radmin_debug.log` in either the radmin container, radius container or log volume.