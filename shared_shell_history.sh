# Guard clause to prevent duplicate import
if [[ -n "${__shared_shell_history_imported:-}" ]]; then
    echo "shared_shell_history is already imported"
    return 0
fi

__shared_shell_history_imported="defined"

INSTALLATION_PATH=$(dirname $(realpath $0))

source $INSTALLATION_PATH/config.sh
$INSTALLATION_PATH/create_table_if_not_exists.sh $SHARED_SHELL_HISTORY_DB_URL
source $INSTALLATION_PATH/bind_menu_key.sh

# Helper functions to activate/deactivate interactive mode
__interactive_mode_on() {
    __shared_shell_history_interactive_mode="on"
}

__interactive_mode_off() {
    __shared_shell_history_interactive_mode=""
}

# enable interactive mode by default
__interactive_mode_on


if (( BASH_VERSINFO[0] > 5 || (BASH_VERSINFO[0] == 5 && BASH_VERSINFO[1] >= 1) )); then
    PROMPT_COMMAND+=('__interactive_mode_on')
else
    # shellcheck disable=SC2179 # PROMPT_COMMAND is not an array in bash <= 5.0
    PROMPT_COMMAND+=$'\n__interactive_mode_on'
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
    if [[ -z "${__shared_shell_history_interactive_mode:-}" ]]; then
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
            __interactive_mode_off
        fi
    fi

    if  __in_prompt_command "${BASH_COMMAND:-}"; then
        # If we're executing something inside our prompt_command then we don't
        # want to call preexec. Bash prior to 3.1 can't detect this at all :/
        __interactive_mode_off
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

    $INSTALLATION_PATH/submit_to_database.sh $SHARED_SHELL_HISTORY_DB_URL "$this_command"
    last_history_id=$this_command_history_id
}

trap '__shared_shell_history_preexec' DEBUG
