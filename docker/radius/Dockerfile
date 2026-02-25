FROM freeradius/freeradius-server:3.2.8-alpine

RUN apk add postgresql

COPY docker/radius/raddb/dictionary* /etc/raddb/
COPY docker/radius/raddb/mods-available/* /etc/raddb/mods-available/
COPY docker/radius/raddb/sites-available/* /etc/raddb/sites-available/

COPY docker/radius/raddb/mods-config/files/authorize /etc/raddb/mods-config/files/authorize
COPY docker/radius/raddb/mods-config/sql/main/postgresql/queries.conf /etc/raddb/mods-config/sql/main/postgresql/queries.conf

COPY docker/radius/raddb/policy.d/canonicalization /etc/raddb/policy.d/canonicalization

COPY docker/radius/raddb/clients.conf /etc/raddb/clients.conf

# Enable mods

RUN ln -s /etc/raddb/mods-available/rest /etc/raddb/mods-enabled/rest && \
    ln -s /etc/raddb/mods-available/sql /etc/raddb/mods-enabled/sql
# RUN ln -s /etc/raddb/mods-available/ldap /etc/raddb/mods-enabled/ldap

RUN ln -s ./etc/raddb/sites-available/control-socket /etc/raddb/sites-enabled/control-socket


COPY docker/radius/pre-start.sh /docker-entrypoint.d/pre-start.sh
RUN chmod u+x /docker-entrypoint.d/pre-start.sh