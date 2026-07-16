# CNaaS NAC - Network Admission Control  

Software to automate management of a campus network(LAN). This is an
open source software developed as part of SUNETs managed service.

CNaaS NAC provides a way for clients to authenticate themselves using
IEEE 802.1X and MAB.

## Features
- Automatic discovery of MAB clients
- Periodic cleanup of inactive clients.
- Replication between primary and secondary server.
- LDAP integration.
- REST JSON API.
- [Web UI](https://github.com/SUNET/cnaas-nac-front) written in React.

## Components

### High level
![CNaaS component architecture](nac-components-20201209.png)

### Low level
```mermaid
flowchart TB
    %% Services
    subgraph Docker_Compose["Docker"]

        nac_api_external["nac_api_external<br/>FastAPI External API"]
        
        nac_api_internal["nac_api_internal<br/>FastAPI Internal API"]

        nac_radius["nac_radius<br/>FreeRADIUS<br/>UDP 1812 Authentication<br/>UDP 1813 Accounting"]

        nac_radmin["nac_radmin<br/>Radius Admin"]

        nac_postgres[("nac_postgres<br/>PostgreSQL 18<br/>Port: 5432:5432<br/>Database: nac")]

    end

    %% External access
    client["External Clients"]
    radius_client["RADIUS Clients"]

    client -->|HTTP| nac_api_external

    radius_client -->|UDP 1812/1813| nac_radius

    %% Runtime communication
    nac_api_external <-->|SQL| nac_postgres
    nac_api_internal <-->|SQL| nac_postgres
    nac_radmin <-->|SQL| nac_postgres

    nac_radius -->|REST| nac_api_internal

    %% Volumes
    subgraph Volumes["Shared Volumes"]

        postgres_data["nac-postgres-data"]

        radius_certs["nac-freeradius-certs"]

        radius_logs["nac-freeradius-logs"]

        radius_socket["nac-freeradius-socket"]

        api_certs["nac-api-certs"]

    end

    nac_postgres --- postgres_data

    nac_radius --- radius_certs
    nac_radius --> |Writes logs| radius_logs
    nac_radius --> |Exposes radiusd socket| radius_socket
    nac_radius --- api_certs

    nac_radmin --> |Talks to radiusd socket| radius_socket
    nac_radmin --> |Monitor radius debug logs| radius_logs
```
