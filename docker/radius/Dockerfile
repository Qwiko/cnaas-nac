FROM freeradius/freeradius-server:3.2.10-alpine

RUN apk add postgresql python3 py3-jinja2 py3-pydantic-settings

COPY docker/radius/raddb/dictionary /opt/etc/raddb/dictionary
COPY docker/radius/raddb/mods-available/* /opt/etc/raddb/mods-available/
COPY docker/radius/raddb/sites-available/* /opt/etc/raddb/sites-available/

COPY docker/radius/raddb/mods-config/files/authorize /opt/etc/raddb/mods-config/files/authorize
COPY docker/radius/raddb/mods-config/sql/main/postgresql/queries.conf /opt/etc/raddb/mods-config/sql/main/postgresql/queries.conf

COPY docker/radius/raddb/policy.d/canonicalization /opt/etc/raddb/policy.d/canonicalization

COPY docker/radius/raddb/clients.conf /opt/etc/raddb/clients.conf

COPY docker/radius/raddb/proxy.conf.j2 /opt/etc/raddb/proxy.conf.j2
COPY docker/radius/raddb/radiusd.conf /opt/etc/raddb/radiusd.conf

# Enable mods
RUN ln -s /opt/etc/raddb/mods-available/rest /opt/etc/raddb/mods-enabled/rest && \
    ln -s /opt/etc/raddb/mods-available/sql /opt/etc/raddb/mods-enabled/sql && \
    ln -s /opt/etc/raddb/mods-available/ldap /opt/etc/raddb/mods-enabled/ldap && \
    ln -s /opt/etc/raddb/mods-available/json /opt/etc/raddb/mods-enabled/json

# Create symlink for enabled sites
RUN ln -s /opt/etc/raddb/sites-available/control-socket /opt/etc/raddb/sites-enabled/control-socket && \
    ln -s /opt/etc/raddb/sites-available/dynamic-clients /opt/etc/raddb/sites-enabled/dynamic-clients

# Copy over scripts
COPY docker/radius/render_config.py /docker-entrypoint.d/00_render_config.py
COPY docker/radius/entrypoint.sh /docker-entrypoint.sh

RUN chmod +x \ 
        /docker-entrypoint.d/00_render_config.py \
        /docker-entrypoint.sh

RUN addgroup -g 1001 radius \
    && adduser -D -u 1001 -G radius radius

RUN chown -R radius:radius /opt/etc/raddb \
    && mkdir -p /opt/var/log/radius && chown -R radius:radius /opt/var/log/radius \
    && mkdir -p /opt/var/run/radiusd && chown -R radius:radius /opt/var/run/radiusd && \
    chmod 755 /opt/var/run/radiusd

USER radius