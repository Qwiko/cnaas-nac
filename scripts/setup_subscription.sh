#!/usr/bin/env bash
set -e

PEER_HOST=${1:-"nac-02"}
DB_NAME=${2:-"nac"}
DB_USER=${3:-"cnaas"}
DB_PASSWORD=${4:-"cnaas"}

SUB_NAME="subscription_${PEER_HOST//-/_}"

echo "Setting up subscription to $PEER_HOST, db: $DB_NAME"

psql -U "$DB_USER" -d $DB_NAME <<-EOSQL
    CREATE SUBSCRIPTION $SUB_NAME 
    CONNECTION 'host=$PEER_HOST dbname=$DB_NAME user=$DB_USER password=$DB_PASSWORD' 
    PUBLICATION publication 
    WITH (origin = none);
EOSQL
