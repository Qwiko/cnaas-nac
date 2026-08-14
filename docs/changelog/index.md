# Changelog

## 2.0.0

Version 2.0.0 introduces a complete rewrite of the CNaaS-NAC platform with a modern FastAPI-based architecture and a broad set of new capabilities.

- Internal API rewritten for a stateless design that can be scaled horizontally.
- External API rewritten for improved structure and extensibility.
- Added OIDC support.
- Introduced the new radmin component, which communicates directly with FreeRADIUS through the radiusd socket for tasks such as live debugging and clearing dynamic clients.
- Updated container images and base images.
- Added support for templating FreeRADIUS configuration from environment variables.
- Added LDAP integration for FreeRADIUS.
- Added live debugging functionality.
- Added RBAC support with granular permissions for API access.
- Added policy-based authorization with support for MAB and EAP handling, port locking, and flexible AND/OR condition evaluation.
- Added CoA support for dynamically bouncing switch ports.
- Added automated cleanup tasks for stale endpoints and authentication/accounting data.
- Redesigned database synchronization with PostgreSQL replication.
