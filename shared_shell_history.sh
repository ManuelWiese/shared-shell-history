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
#    - Filters out commands based on interactive mode and other criteria.
#    - Extracts the last executed command and saves it to the database.
# 5. Interactive Mode: Maintains a state to determine when to capture commands, toggled by the prompt command.
#
# Usage:
# Source this script in your Bash profile (e.g., .bashrc or .bash_profile):
#   source /path/to/shared_shell_history.sh
#
# Dependencies:
# - Bash version 5.1 or higher.
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


$SHARED_SHELL_HISTORY_BASE_DIR/create_table_if_not_exists.sh $SHARED_SHELL_HISTORY_DB_URL
source $SHARED_SHELL_HISTORY_BASE_DIR/bind_menu_key.sh

# Helper functions to activate/deactivate interactive mode
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

__trim_whitespace() {
    local var=${1:?} text=${2:-}
    text="${text#"${text%%[![:space:]]*}"}"   # remove leading whitespace characters
    text="${text%"${text##*[![:space:]]}"}"   # remove trailing whitespace characters
    printf -v "$var" '%s' "$text"
}


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


__latest_history_id() {
    echo $(
        export LC_ALL=C
        HISTTIMEFORMAT='' builtin history 1 | awk '{ print $1 }'
	)
}

last_history_id=$(__latest_history_id)


__shared_shell_history_preexec() {
    # Don't invoke preexecs if we are inside of another preexec.
    if (( __inside_preexec > 0 )); then
      return
    fi
    local __inside_preexec=1

    if [[ -n "${COMP_LINE:-}" ]]; then
        # We're in the middle of a completer. This obviously can't be
        # an interactively issued command.
        return
    fi
    if [[ -z "${__command_capture_enabled:-}" ]]; then
        # We're doing something related to displaying the prompt.  Let the
        # prompt set the title instead of me.
        return
    else
        # If we're in a subshell, then the prompt won't be re-displayed to put
        # us back into interactive mode, so let's not set the variable back.
        # In other words, if you have a subshell like
        #   (sleep 1; sleep 2)
        # You want to see the 'sleep 2' as a set_command_title as well.
        if [[ 0 -eq "${BASH_SUBSHELL:-}" ]]; then
            __disable_command_capture
        fi
    fi

    if  __in_prompt_command "${BASH_COMMAND:-}"; then
        # If we're executing something inside our prompt_command then we don't
        # want to call preexec. Bash prior to 3.1 can't detect this at all :/
        __disable_command_capture
        return
    fi

    # we can get the command using 'builtin history 1'
    # save this in a local variable called this_command
    # Remove timestamp using HISTTIMEFORMAT=''
    # Remove the command-number using sed
    local this_command

    this_command=$(
        export LC_ALL=C
        HISTTIMEFORMAT='' builtin history 1 | sed '1 s/^ *[0-9][0-9]*[* ] //'
		)
    this_command_history_id=$(__latest_history_id)

    if [[ "$this_command_history_id" == "$last_history_id" ]]; then
        return
    fi

    $SHARED_SHELL_HISTORY_BASE_DIR/submit_to_database.sh $SHARED_SHELL_HISTORY_DB_URL "$this_command"
    last_history_id=$this_command_history_id
}

trap '__shared_shell_history_preexec' DEBUG
