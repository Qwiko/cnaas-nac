#!/usr/bin/env bash
set -e

START_POINT=${1:-1}
OFFSET=${2:-1}
DB_NAME=${3:-"nac"}
DB_USER=${4:-"cnaas"}
DB_SERVER=${5:-"localhost"}
DB_PORT=${6:-"5432"}

echo "Configuring sequences for start: $START_POINT, offset: $OFFSET."
echo "Using user: $DB_USER for db: $DB_NAME."

# Fetches all sequence names from the public schema
SEQUENCES=$(psql -U "$DB_USER" -d "$DB_NAME" -t -A -c "
    SELECT sequence_name 
    FROM information_schema.sequences 
    WHERE sequence_schema = 'public';
")

if [ -z "$SEQUENCES" ]; then
	echo "No sequences found in database $DB_NAME."
	exit 0
fi

for SEQ in $SEQUENCES; do
	echo "----------------------------------------"
	echo "Processing sequence: $SEQ"

	# Find the table and column associated with this sequence
	ASSOC_INFO=$(psql -U "$DB_USER" -d "$DB_NAME" -t -A -F',' -c "
        SELECT t.relname, a.attname
        FROM pg_class s
        JOIN pg_depend d ON d.objid = s.oid
        JOIN pg_class t ON d.refobjid = t.oid
        JOIN pg_attribute a ON (d.refobjid = a.attrelid AND d.refobjsubid = a.attnum)
        WHERE s.relname = '$SEQ' AND s.relkind = 'S';")

	TABLE_NAME=$(echo $ASSOC_INFO | cut -d',' -f1)
	COLUMN_NAME=$(echo $ASSOC_INFO | cut -d',' -f2)

	# Find the highest ID currently in the table
	CURRENT_MAX=$(psql -U "$DB_USER" -d "$DB_NAME" -t -A -c "
        SELECT COALESCE(MAX($COLUMN_NAME), 0)
        FROM $TABLE_NAME
        WHERE $COLUMN_NAME % $OFFSET = $START_POINT % $OFFSET;
        ")

	echo "Table: $TABLE_NAME, Column: $COLUMN_NAME, CURRENT MAX: $CURRENT_MAX"

	# Failsafe if the query failed to return a number
	if ! [[ "$CURRENT_MAX" =~ ^[0-9]+$ ]]; then
		CURRENT_MAX=0
	fi

	# Calculate the next valid ID that matches this server offset
	REMAINDER=$((CURRENT_MAX % OFFSET))
	START_REMAINDER=$((START_POINT % OFFSET))

	if [ "$REMAINDER" -lt "$START_REMAINDER" ]; then
		NEXT_START=$((CURRENT_MAX + (START_REMAINDER - REMAINDER)))
	else
		NEXT_START=$((CURRENT_MAX + (OFFSET - REMAINDER) + START_REMAINDER))
	fi

	if [ "$CURRENT_MAX" -eq 0 ]; then
		NEXT_START=$START_POINT
	fi

	echo "Current Max ID: $CURRENT_MAX -> Next Valid Start ID: $NEXT_START"

	# Execute the ALTER SEQUENCE command
	psql -U "$DB_USER" -d "$DB_NAME" -c "
        ALTER SEQUENCE $SEQ 
        INCREMENT BY $OFFSET 
        RESTART WITH $NEXT_START;
    "
done

echo "----------------------------------------"
echo "Sequence configuration complete!"
