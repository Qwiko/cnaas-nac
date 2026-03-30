#!/usr/bin/env bash
set -e

DB_NAME=${1:-"nac"}
DB_USER=${2:-"cnaas"}

# Create the local publication
psql -U "$DB_USER" -d $DB_NAME <<-EOSQL
    CREATE PUBLICATION publication FOR ALL TABLES;
EOSQL
echo "Publication publication created."
