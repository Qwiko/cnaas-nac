# Environment Variables

The following environment variables can be used to configure different application:

## nac_api

### Shared
Environment variables shared between external and internal mode.

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `POSTGRES_USER` | `string` | "cnaas" | Postgres username |
| `POSTGRES_PASSWORD` | `string` | "cnaas" | Postgres password |
| `POSTGRES_SERVER` | `string` | "nac_postgres" | Postgres server |
| `POSTGRES_PORT` | `int` | 5432 | Postgres port |
| `POSTGRES_DB` | `string` | "nac" | Postgres db name |
| `LOGGING` | `string | int` | `INFO` | Set to `DEBUG` to enable verbose debug logging |
| `ENVIRONMENT` | `string` | `local` when run locally, `production` for the docker image. | Sets the running environment. Mainly used in security functions |

### External specific
| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `OIDC_CLIENT_ID` | `string` | "cnaas-nac" | OIDC client id |
| `OIDC_CLIENT_SECRET` | `string` | "" | OIDC client secret |
| `OIDC_DISCOVERY_URL` | `string` | "" | OIDC discovery url |
| `OIDC_USERINFO_ATTRIBUTE` | `string` | "userinfo" | OIDC userinfo attribute |
| `OIDC_USERNAME_ATTRIBUTE` | `string` | "preferred_username" | userinfo username attribute |
| `OIDC_GROUPS_ATTRIBUTE` | `string` | "roles" | userinfo groups attribute |
| `OIDC_ADMIN_GROUP` | `string` | "admins" | Which OIDC group should map to the admin group |
| `OIDC_ADMIN_USERS` | `list[string]` | [] | Used to manually set users to the internal admin group |
| `SECRET_KEY` | `string` | "replace_this_with_a_secure_random_string" | Used for session middleware |
| `JWT_EXPIRATION_MINUTES` | `int` | 60 | How long the jwt access token should be valid |
| `FRONTEND_CALLBACK_URL` | `string` | "/#/auth-callback" | Frontend callback during OIDC login |

### Internal specific
| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `PRUNING_DISABLED` | `bool` | False | Disable pruning by settings this to true |
| `ENDPOINT_MAB_DISCOVERED_RETENTION_DAYS` | `int` | 30 | How long to keep discovered MAB endpoints before they are pruned |
| `ENDPOINT_MAB_PENDING_RETENTION_DAYS` | `int` | 30 | How long to keep pending MAB endpoints before they are pruned |
| `ENDPOINT_MAB_REJECTED_RETENTION_DAYS` | `int` | 30 | How long to keep rejected MAB endpoints before they are pruned |
| `ENDPOINT_EAP_REJECTED_RETENTION_DAYS` | `int` | 30 | How long to keep rejected EAP endpoints before they are pruned |
| `ENDPOINT_MAB_AUTHORIZED_RETENTION_DAYS` | `int` | 90 | How long to keep authorized MAB endpoints before they are pruned |
| `ENDPOINT_EAP_AUTHORIZED_RETENTION_DAYS` | `int` | 90 | How long to keep authorized EAP endpoints before they are pruned |
| `RADACCT_RETENTION_DAYS` | `int` | 90 | How long to keep radacct(sessions) before they are pruned |
| `RADPOSTAUTH_RETENTION_DAYS` | `int` | 90 | How long to keep radpostauth(authentications) before they are pruned |

## nac_radius

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `PRE_START_BASE_FOLDER` | `string` | "/etc/raddb" | Where the init-script should look for template files during bootup. |
| `RADIUS_PROXY_CONFIGS` | `list (object)` | `[]` | See: [RADIUS_PROXY_CONFIGS](#radius_proxy_configs). |
| `RADIUS_EAP_CONFIGS` | `list (object)` | `[]` | See: [RADIUS_EAP_CONFIGS](#radius_eap_configs). |
| `LDAP_CONFIGS` | `list (object)` | `[]` | See: [LDAP_CONFIGS](#ldap_configs). |


### Examples

#### RADIUS_PROXY_CONFIGS
```bash
RADIUS_PROXY_CONFIGS: |
    [
        {
            "realm": "example.org",
            "pool_name": "" # Optional
            "pool_type": "" # Optional, default fail-over
            "servers": [
                {
                    "name": "radius",
                    "ipaddr": "radius.example.org",
                    "port": "1812", # Optional, default 1812
                    "secret": "testing123"
                }
            ]
        }
    ]
```

#### RADIUS_EAP_CONFIGS
!!! warning "WIP"
    Not yet fully implemented.

```bash
RADIUS_EAP_CONFIGS: |
    [
        {
            "name": "",
            "domain": "",
            "priv_key": "",
            "cert": "",
            "ca": "",
            "check_crl": false,
            "crl_url": ""
        }
    ]
```

#### LDAP_CONFIGS
```bash
LDAP_CONFIGS: |
    [
        {
            "ad_username_attr": "mail", # Optional, default sAMAccountName
            "ad_member_attr": "", # Optional, default: memberOf
            "ad_member_filter":""  # Optionally used instead of ad_member_attr
            "ad_domain": "example.org", 
            "ad_server": "server1.example.org", # Optional hostname other than the domain name
            "ad_username": "", # Bind user
            "ad_password": "",
            "ad_base_dn": ""
        }
    ]
```