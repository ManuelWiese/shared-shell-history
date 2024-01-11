#!/bin/bash

# Define the target directory
TARGET_DIR="$HOME/.shared_shell_history"

# Create the target directory if it doesn't exist
mkdir -p "$TARGET_DIR"

BASE_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)

# Copy relevant files to the target directory
cp -r "$BASE_DIR/shared_shell_history/*" "$TARGET_DIR/"

# Function to ask for a configuration value
ask_for_value() {
    local var_name=$1
    local default_value=$2
    local user_input

    read -p "Enter value for $var_name [$default_value]: " user_input
    echo "${user_input:-$default_value}"
}

# Default values
DEFAULT_DB_URL="sqlite:///$TARGET_DIR/history.db"
DEFAULT_MENU_KEY="\C-b"

# Check if the DB URL value is provided as an argument or ask for it
DB_URL=${1:-$(ask_for_value "SHARED_SHELL_HISTORY_DB_URL" "$DEFAULT_DB_URL")}

# Use default for SHARED_SHELL_HISTORY_MENU_KEY unless provided as second argument
MENU_KEY=${2:-$DEFAULT_MENU_KEY}

# Create the config.sh file
cat > "$TARGET_DIR/config.sh" <<EOL
export SHARED_SHELL_HISTORY_DB_URL="$DB_URL"
export SHARED_SHELL_HISTORY_MENU_KEY="$MENU_KEY"
EOL

# Add a source command to .bashrc if not already present
BASHRC="$HOME/.bashrc"
SOURCE_STRING="source $TARGET_DIR/shared_shell_history.sh"

if ! grep -q "$SOURCE_STRING" "$BASHRC"; then
    echo "$SOURCE_STRING" >> "$BASHRC"
    echo "Added source command to $BASHRC"
else
    echo "Source command already present in $BASHRC"
fi

echo "Installation complete."
