TARGET_DIR="$HOME/.shared_shell_history"
rm -fr $TARGET_DIR
if [ $? ]; then
    echo "Uninstall error: target folder not present"
fi

BASHRC="$HOME/.bashrc"

SOURCE_STRING="source $TARGET_DIR/shared_shell_history.sh"

#Escapes slashes of the source string for usage in sed
SOURCE_STRING=$(echo "$SOURCE_STRING" | sed 's/\//\\\//g')

sed -i "/^$SOURCE_STRING/D" $BASHRC