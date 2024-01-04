#!/bin/bash

if ! command -v psql &> /dev/null
then
    echo "shared_shell_history: psql installation not found" >&2
    exit 1
fi

DB_URL=$1
COMMAND=$2

path=$(realpath $PWD)
host=$(hostname)

PSQL_RETURN_CODE=$(psql $DB_URL -q -c "INSERT INTO bash_commands (user_name, host, path, command, venv) VALUES ('$USER', '$host', '$path', '$COMMAND', '$VIRTUAL_ENV')")

case "$PSQL_RETURN_CODE" in
    "1")
        echo "shared_shell_history: psql fatal error" >&2
    ;;
    "2")
        echo "shared_shell_history: psql connection to database lost" >&2
    ;;
    "3")
        echo "shared_shell_history: psql an error occurred in a script" >&2
    ;;
esac