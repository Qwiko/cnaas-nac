#!/bin/bash
set -e

if [ "$1" = 'external' ]; then
    set -- fastapi run cnaas_nac/api_external/main.py --port 8000
elif [ "$1" = 'internal' ]; then
    set -- fastapi run cnaas_nac/api_internal/main.py --port 8000
else
    echo "Mode: $1 is not supported." >& 2
    exit 1
fi

# Execute the command
exec "$@"