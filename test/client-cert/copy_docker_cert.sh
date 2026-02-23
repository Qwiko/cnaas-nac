# Copy the CA certificate

docker cp docker-nac_radius-1:/etc/raddb/certs/ca.pem .
docker cp docker-nac_radius-1:/etc/raddb/certs/client.pem .
docker cp docker-nac_radius-1:/etc/raddb/certs/client.key .


docker cp ca.pem clab-cnaas-nac-e2e-alpine-c1:/tmp
docker cp client.pem clab-cnaas-nac-e2e-alpine-c1:/tmp
docker cp client.key clab-cnaas-nac-e2e-alpine-c1:/tmp

docker cp wpa_supplicant.conf clab-cnaas-nac-e2e-alpine-c1:/tmp
