#!/bin/sh
set -e

PATH=/opt/sbin:/opt/bin:$PATH
export PATH

if [ -d "/docker-entrypoint.d" ]; then
    echo "$0: Looking for entrypoint scripts in /docker-entrypoint.d/..."
    for f in /docker-entrypoint.d/*; do
        # Handle the case where the directory is empty
        [ -e "$f" ] || continue 
        
        case "$f" in
            *.sh)
                if [ -x "$f" ]; then
                    echo "$0: Executing $f"
                    "$f"
                else
                    echo "$0: Sourcing $f"
                    . "$f"
                fi
                ;;
            *)
                if [ -x "$f" ]; then
                    echo "$0: Executing $f"
                    "$f"
                else
                    echo "$0: Ignoring $f (not executable)"
                fi
                ;;
        esac
    done
    echo "$0: Finished running entrypoint scripts."
fi

# this if will check if the first argument is a flag
# but only works if all arguments require a hyphenated flag
# -v; -SL; -f arg; etc will work, but not arg1 arg2
if [ "$#" -eq 0 ] || [ "${1#-}" != "$1" ]; then
    set -- radiusd "$@"
fi

# check for the expected command
if [ "$1" = 'radiusd' ]; then
    shift
    exec radiusd -f "$@"
fi

# debian people are likely to call "freeradius" as well, so allow that
if [ "$1" = 'freeradius' ]; then
    shift
    exec radiusd -f "$@"
fi

# else default to run whatever the user wanted like "bash" or "sh"
exec "$@"