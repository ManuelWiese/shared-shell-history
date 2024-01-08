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
    python3 search_command.py --tmp_file $tempfile --db_url $SHARED_SHELL_HISTORY_DB_URL --user $USER

    command=$(cat $tempfile)
    rm $tempfile

    READLINE_LINE=$command
    READLINE_POINT=${#command}
}

bind -x '"'$SHARED_SHELL_HISTORY_MENU_KEY'":search_and_insert_from_history'
