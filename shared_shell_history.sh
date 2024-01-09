#!/bin/bash
# shared_shell_history.sh
#
# This script is designed to capture and save Bash command history into a PostgreSQL database. 
# It is meant to be sourced, not executed directly, allowing it to integrate seamlessly into the 
# existing shell environment.
#
# How it Works:
# 1. Guard Clause: Prevents re-sourcing the script if it has already been sourced, avoiding duplicate imports.
# 2. Configuration: Sources external configuration scripts and sets up necessary environment variables.
# 3. Database Initialization: Checks if the required table exists in the PostgreSQL database, and creates it if not.
# 4. Command History Capture:
#    - Utilizes the DEBUG trap to intercept commands before they are executed.
#    - Filters out commands based on command capture mode and other criteria.
#    - Extracts the last executed command and saves it to the database.
# 5. Command Capture Mode: Maintains a state to determine when to capture commands, toggled by the prompt command.
#
# Usage:
# Source this script in your Bash profile (e.g., .bashrc or .bash_profile):
#   source /path/to/shared_shell_history.sh
#
# Dependencies:
# - PostgreSQL database access and proper configuration set in config.sh.
# - Required external scripts (config.sh, create_table_if_not_exists.sh, bind_menu_key.sh, submit_to_database.sh).

SHARED_SHELL_HISTORY_BASE_DIR=$(dirname "$(realpath "$0")")

if [ -f "${SHARED_SHELL_HISTORY_BASE_DIR}/config.sh" ]; then
    source "${SHARED_SHELL_HISTORY_BASE_DIR}/config.sh"
else
    echo "Error: config.sh not found in ${SHARED_SHELL_HISTORY_BASE_DIR}"
    echo "To set up config.sh:"
    echo "1. Create a new file named config.sh in the same directory as shared_shell_history.sh."
    echo "2. Add the following lines to the file, replacing with your own values:"
    echo '   SHARED_SHELL_HISTORY_DB_URL="postgresql://postgresuser:password@server:port/database"'
    echo '   SHARED_SHELL_HISTORY_MENU_KEY="\C-b" # Replace with your preferred key combination'
    echo "3. Save the file and re-source shared_shell_history.sh."
    exit 1
fi

# Guard clause to prevent duplicate import
if [[ -n "${__shared_shell_history_imported:-}" ]]; then
    echo "shared_shell_history.sh has already been sourced. Skipping re-import."
    return 0
fi

__shared_shell_history_imported="defined"

source "${SHARED_SHELL_HISTORY_BASE_DIR}/run_python.sh"
# Create table if it does not exist already
run_python "${SHARED_SHELL_HISTORY_BASE_DIR}/create_table_if_not_exists.py" --database "${SHARED_SHELL_HISTORY_DB_URL}"

# Helper functions to activate/deactivate command capture
__enable_command_capture() {
    __command_capture_enabled="on"
}

__disable_command_capture() {
    __command_capture_enabled=""
}

# enable interactive mode by default
__enable_command_capture


if (( BASH_VERSINFO[0] > 5 || (BASH_VERSINFO[0] == 5 && BASH_VERSINFO[1] >= 1) )); then
    PROMPT_COMMAND+=('__enable_command_capture')
else
    # shellcheck disable=SC2179 # PROMPT_COMMAND is not an array in bash <= 5.0
    PROMPT_COMMAND+=$'\n__enable_command_capture'
fi

# __trim_whitespace
#
# Trims leading and trailing whitespace from a given string.
#
# This function takes two arguments:
#   1. var: A variable name where the trimmed result will be stored.
#   2. text: The string that needs whitespace trimming.
#
# If 'text' is not provided, the function will default to an empty string.
# The result of the trimming operation is stored in the variable named by 'var'.
# This function uses Bash's parameter expansion capabilities to remove 
# whitespace without spawning subshells or using external commands like 'sed' or 'awk'.
#
# Usage:
#   __trim_whitespace result_var "  some text with space  "
#   echo $result_var  # Output: "some text with space"
#
__trim_whitespace() {
    local var=${1:?} text=${2:-}
    text="${text#"${text%%[![:space:]]*}"}"   # remove leading whitespace characters
    text="${text%"${text##*[![:space:]]}"}"   # remove trailing whitespace characters
    printf -v "$var" '%s' "$text"
}


# __in_prompt_command
#
# Checks if a given command is part of the PROMPT_COMMAND array.
#
# This function is designed to determine whether a specified command (argument to this function)
# is one of the commands executed as part of the Bash PROMPT_COMMAND. PROMPT_COMMAND is a 
# special Bash variable that holds commands to be executed before each prompt. This is useful 
# to ensure that certain operations are not redundantly performed if they are already a part of 
# the prompt's setup.
#
# Arguments:
#   1. The command to check for in the PROMPT_COMMAND array.
#
# Returns:
#   - 0 (success) if the command is found in PROMPT_COMMAND.
#   - 1 (failure) if the command is not found in PROMPT_COMMAND.
#
# Usage:
#   if __in_prompt_command "some_command"; then
#       echo "The command is part of PROMPT_COMMAND."
#   else
#       echo "The command is not in PROMPT_COMMAND."
#   fi
#
__in_prompt_command() {

    local prompt_command_array IFS=$'\n;'
    read -rd '' -a prompt_command_array <<< "${PROMPT_COMMAND[*]:-}"

    local trimmed_arg
    __trim_whitespace trimmed_arg "${1:-}"

    local command trimmed_command
    for command in "${prompt_command_array[@]:-}"; do
        __trim_whitespace trimmed_command "$command"
        if [[ "$trimmed_command" == "$trimmed_arg" ]]; then
            return 0
        fi
    done

    return 1
}


# __latest_history_id
#
# Retrieves the ID of the most recent command in the Bash history.
#
# This function uses the `history` builtin to obtain the latest command's ID.
# It temporarily sets the locale to 'C' and disables the HISTTIMEFORMAT to ensure
# consistent parsing of the history output. The function then uses `awk` to extract
# and return the command ID.
#
# Returns:
#   The ID of the most recent command in the Bash history.
#
# Usage:
#   latest_id=$(__latest_history_id)
#   echo "The most recent command ID is: $latest_id"
#
__latest_history_id() {
    export LC_ALL=C
    HISTTIMEFORMAT='' builtin history 1 | awk '{ print $1 }'
}

# __latest_history_command
#
# Retrieves the latest command from the Bash history.
#
# This function fetches the most recent command entered in the Bash shell. 
# It uses the `history` builtin to get the command and `sed` to parse out 
# the command text, excluding its history ID and any leading spaces. 
#
# Returns:
#   The most recent command from the Bash history.
#
# Usage:
#   latest_command=$(__latest_history_command)
#   echo "The most recent command is: $latest_command"
#
__latest_history_command() {
    export LC_ALL=C
    HISTTIMEFORMAT='' builtin history 1 | sed '1 s/^ *[0-9][0-9]*[* ] //'
}


# __submit_last_command_to_database
#
# Submits the latest command from the Bash history to a PostgreSQL database.
#
# This function retrieves the most recent command entered in the Bash shell using the 
# __latest_history_command function. It then calls an external script, 'submit_to_database.sh',
# located in the SHARED_SHELL_HISTORY_BASE_DIR directory, passing it the database URL and the 
# command to be submitted.
#
# The SHARED_SHELL_HISTORY_DB_URL variable should contain the PostgreSQL database URL.
#
# Usage:
#   __submit_last_command_to_database
#
__submit_last_command_to_database() {
    local user="$USER"
    local host="$(hostname)"
    local path="$(realpath ${PWD})"
    local command=$(__latest_history_command)
    local venv="$VIRTUAL_ENV"

    local script_path="${SHARED_SHELL_HISTORY_BASE_DIR}/insert_command.py"

    # Call run_python with all necessary arguments
    run_python "$script_path" \
               --command "$command" \
               --database "$SHARED_SHELL_HISTORY_DB_URL" \
               --host "$host" \
               --path "$path" \
               --user "$user" \
               --venv "$venv"
}


# __shared_shell_history_preexec
#
# A pre-execution hook that captures and submits the latest Bash command to the database.
#
# This function is designed to be called before each command execution in an interactive Bash session. 
# It performs several checks to determine whether the latest command should be captured and submitted 
# to a database. The function:
#   - Avoids recursion by checking if it's already inside a pre-execution context.
#   - Skips command capture during command-line completion.
#   - Checks if command capture is enabled.
#   - Disables command capture for subsequent commands if inside a subshell.
#   - Avoids capturing commands that are part of PROMPT_COMMAND.
#   - Prevents duplicate captures by comparing the latest history ID with the last captured ID.
#   - Calls __submit_last_command_to_database to submit the command.
#
# Usage:
#   This function is intended to be set as a trap for the DEBUG signal in an interactive shell.
#   trap '__shared_shell_history_preexec' DEBUG
#
__shared_shell_history_preexec() {
    # Don't invoke preexecs if we are inside of another preexec.
    if (( __inside_preexec > 0 )); then
      return
    fi
    local __inside_preexec=1

    if [[ -n "${COMP_LINE:-}" ]]; then
        # We're in the middle of a completer.
	# This obviously can't be an issued command.
        return
    fi
    if [[ -z "${__command_capture_enabled:-}" ]]; then
	# command capture is disabled
        return
    fi

    if [[ 0 -eq "${BASH_SUBSHELL:-}" ]]; then
	# Disable command capture for the following commands if we are in a subshell
	# The current/first command is captured
        __disable_command_capture
    fi

    if  __in_prompt_command "${BASH_COMMAND:-}"; then
        # If we're executing something inside our prompt_command then we don't
        # want to call preexec
        __disable_command_capture
        return
    fi

    local latest_history_id=$(__latest_history_id)
    if [[ "$latest_history_id" == "$SHARED_SHELL_HISTORY_LAST_ID" ]]; then
	# If no new command was added to the history (e.g. a key combination was pressed)
	# do not capture the last command, this would add duplicates.
        return
    else
	SHARED_SHELL_HISTORY_LAST_ID=$latest_history_id
    fi

    __submit_last_command_to_database
}


# search_and_insert_from_history
#
# Searches the command history and inserts a selected command into the current command line.
#
# This function facilitates an advanced command retrieval feature where a user can search
# through their command history using a Python script. The retrieved command is
# then inserted into the current command line in the shell, ready for execution or further editing.
# The function achieves this by creating a temporary file to store the retrieved command,
# reading this command into the shell, and then setting it as the current line in the readline buffer.
# It is intended to be used in conjunction with a key binding that activates the function.
#
# The function relies on:
#   - A Python script ('search_command.py') for searching the command history.
#   - The SHARED_SHELL_HISTORY_DB_URL for the database connection.
#   - The 'mktemp' utility to create a temporary file for intermediate storage.
#
# Usage:
#   To use this function, bind it to a key combination in the shell:
#   bind -x '"'$SHARED_SHELL_HISTORY_MENU_KEY'":search_and_insert_from_history'
#
#   When the key combination is pressed, the function will be triggered.
#
search_and_insert_from_history() {
    tempfile=$(mktemp /tmp/command_XXXX)
    run_python search_command.py --tmp_file $tempfile --db_url $SHARED_SHELL_HISTORY_DB_URL --user $USER

    command=$(cat $tempfile)
    rm $tempfile

    READLINE_LINE=$command
    READLINE_POINT=${#command}
}


# init SHARED_SHELL_HISTORY_LAST_ID when sourcing this file the first time
SHARED_SHELL_HISTORY_LAST_ID=$(__latest_history_id)

trap '__shared_shell_history_preexec' DEBUG

bind -x '"'$SHARED_SHELL_HISTORY_MENU_KEY'":search_and_insert_from_history'
