#!/bin/bash
set -e

# TODO changed allowed forwarded-allow-ips to "*" for now, but should be changed to specific IPs in production
if [ "$1" = 'external' ]; then
    set -- uvicorn src.cnaas_nac.api_external.main:app --host 0.0.0.0 --port 8000 --forwarded-allow-ips="*"
elif [ "$1" = 'internal' ]; then
    set -- uvicorn src.cnaas_nac.api_internal.main:app --host 0.0.0.0 --port 8000 --forwarded-allow-ips="*"
else
    echo "Mode: $1 is not supported." >& 2
    exit 1
fi

# Execute the command
exec "$@"