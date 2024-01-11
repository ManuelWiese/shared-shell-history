#!/bin/bash

# Define the target directory
TARGET_DIR="$HOME/.shared_shell_history"

# Check if the target directory exists and remove it
if [ -d "$TARGET_DIR" ]; then
    rm -rf "$TARGET_DIR"
    echo "Removed directory: $TARGET_DIR"
else
    echo "Uninstall error: Target folder not present."
    exit 1
fi

# Define path to .bashrc
BASHRC="$HOME/.bashrc"

# Define the source string to be removed
SOURCE_STRING="source $TARGET_DIR/shared_shell_history.sh"

# Check if .bashrc contains the source string
if grep -qF "$SOURCE_STRING" "$BASHRC"; then
    # Use sed to delete the line containing the source string
    # use | as delimiter
    sed -i "\|$SOURCE_STRING|d" "$BASHRC"
    echo "Removed source command from $BASHRC"
else
    echo "Source command not found in $BASHRC"
fi

echo "Uninstallation complete."
