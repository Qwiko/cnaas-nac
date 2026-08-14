[![Python 3.14](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/downloads/release/python-3143/)

# CNaaS NAC

Campus Network-as-a-Service - Network Admission Control

[![Build Status](https://github.com/sunet/cnaas-nac/actions/workflows/pytest.yml/badge.svg)](https://github.com/sunet/cnaas-nac/actions/workflows/pytest.yml)

Software to automate management of a campus network(LAN). This is an
open source software developed as part of SUNETs managed service.

CNaaS NAC provides a way for clients to authenticate themselves using
IEEE 802.1X and MAB.

Features:

- Automatic discovery of MAB clients.
- Periodic cleanup of inactive clients.
- Replication between primary and secondary server.
- LDAP integration.
- REST JSON API.
- [Web UI](https://github.com/SUNET/cnaas-nac-front) written in React.

## Components

![CNaaS component architecture](nac-components-20201209.png?raw=true)
