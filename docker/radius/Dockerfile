FROM freeradius/freeradius-server:3.2.8-alpine

RUN apk add postgresql python3 py3-jinja2 py3-pydantic-settings

COPY docker/radius/raddb/dictionary* /etc/raddb/
COPY docker/radius/raddb/mods-available/* /etc/raddb/mods-available/
COPY docker/radius/raddb/sites-available/* /etc/raddb/sites-available/

COPY docker/radius/raddb/mods-config/files/authorize /etc/raddb/mods-config/files/authorize
COPY docker/radius/raddb/mods-config/sql/main/postgresql/queries.conf /etc/raddb/mods-config/sql/main/postgresql/queries.conf

COPY docker/radius/raddb/policy.d/canonicalization /etc/raddb/policy.d/canonicalization

COPY docker/radius/raddb/clients.conf /etc/raddb/clients.conf

COPY docker/radius/raddb/dictionary /etc/raddb/dictionary
COPY docker/radius/raddb/dictionary.local /etc/raddb/dictionary.local
COPY docker/radius/raddb/proxy.conf.j2 /etc/raddb/proxy.conf.j2
COPY docker/radius/raddb/radiusd.conf /etc/raddb/radiusd.conf

# Enable mods
RUN ln -s /etc/raddb/mods-available/rest /etc/raddb/mods-enabled/rest && \
    ln -s /etc/raddb/mods-available/sql /etc/raddb/mods-enabled/sql

# RUN 
RUN ln -s /etc/raddb/sites-available/control-socket /etc/raddb/sites-enabled/control-socket && \
    ln -s /etc/raddb/sites-available/dynamic-clients /etc/raddb/sites-enabled/dynamic-clients && \
    ln -s /etc/raddb/mods-available/ldap /etc/raddb/mods-enabled/ldap

COPY docker/radius/render_config.py /docker-entrypoint.d/render_config.py
COPY docker/radius/entrypoint.sh /docker-entrypoint.sh


RUN chmod +x \ 
        /docker-entrypoint.d/render_config.py \
        /docker-entrypoint.sh

RUN mkdir -p /opt/var/run/radiusd && \
    chown -R root:root /opt/var/run/radiusd && \
    chmod 755 /opt/var/run/radiusd