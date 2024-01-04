return_command() {
    tempfile=$(mktemp /tmp/command_XXXX)
    python3 search_command.py --tmp_file $tempfile --db_url $SHARED_SHELL_HISTORY_DB_URL --user $USER

    command=$(cat $tempfile)
    rm $tempfile

    READLINE_LINE=$command
    READLINE_POINT=${#command}
}

bind -x '"'$SHARED_SHELL_HISTORY_MENU_KEY'":return_command'