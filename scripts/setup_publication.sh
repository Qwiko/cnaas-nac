#!/usr/bin/env bash
set -e

DB_NAME=${1:-"nac"}
DB_USER=${2:-"cnaas"}

# Create the local publication
psql -U "$DB_USER" -d $DB_NAME <<-EOSQL
    CREATE PUBLICATION publication FOR TABLES IN SCHEMA public;
EOSQL
echo "Publication publication created."
