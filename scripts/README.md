# Intro
When setting up two nac nodes the databases needs to be in sync.  
To achieve this a multi-master setup can be setup with the postgres publication/subscription system.  
Requries postgres 16.

# Scripts

Replace the nac_radius docker name with the real container name.

## Restart sequences

```bash
# Example: Running on nac-01
cat ./scripts/restart_sequences.sh | docker exec -i nac_radius bash -s -- 1 2 nac cnaas

# Example: Running on nac-02
cat ./scripts/restart_sequences.sh | docker exec -i nac_radius bash -s -- 2 2 nac cnaas
```

## Create local publication

```bash
# Example: Running on nac-01
cat ./scripts/setup_publication.sh | docker exec -i nac_radius bash -s -- nac cnaas

# Example: Running on nac-02
cat ./scripts/setup_publication.sh | docker exec -i nac_radius bash -s -- nac cnaas
```

## Setup subscription
The first attribute is the remote server.  
Use a hostname and if you dont use dns use the local hosts-file.  
Read the script before running to understand what it does.
```bash
# Example: Running on nac-01
cat ./scripts/setup_subscription.sh | docker exec -i nac_radius bash -s -- nac_02 nac cnaas cnaas

# Example: Running on nac-02
cat ./scripts/setup_subscription.sh | docker exec -i nac_radius bash -s -- nac-01 nac cnaas cnaas
```

## Refresh subscription

Must be done after new tables have been added.  
Replace the subscription name with the correct name.  
`copy_data = false` means that the servers will not try to replicate data.  
It just refreshes the subscription so new tables are also included.

```bash
# Example: Running on nac-01
docker exec nac_radius psql -U cnaas -d nac -c "
  ALTER SUBSCRIPTION subscription_nac_02 REFRESH PUBLICATION WITH (copy_data = false);"

# Example: Running on nac-02
docker exec nac_radius psql -U cnaas -d nac -c "
  ALTER SUBSCRIPTION subscription_nac_01 REFRESH PUBLICATION WITH (copy_data = false);"
```