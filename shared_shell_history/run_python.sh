# run_python
#
# Runs a Python command using a specific virtual environment.
#
# This function ensures that a Python script is executed within an isolated virtual environment.
# If the virtual environment doesn't exist at the specified path, it creates one and installs
# dependencies specified in a requirements.txt file. This ensures that the script runs with the
# correct dependencies without affecting the global Python environment. The function is useful
# for consistently running Python scripts with the required dependencies in an isolated environment.
#
# Arguments:
#   - Any arguments or options to be passed to the Python script.
#
# Environment Variables:
#   - SHARED_SHELL_HISTORY_BASE_DIR: Base directory for the shared shell history script.
#     The virtual environment and requirements.txt are expected to be inside this directory.
#
# Usage:
#   run_python my_script.py arg1 arg2
#   - This will execute 'my_script.py' with 'arg1' and 'arg2' as arguments within the virtual environment.
#
run_python() {
    local venv_path="${SHARED_SHELL_HISTORY_BASE_DIR:?}/venv"
    local requirements_path="${SHARED_SHELL_HISTORY_BASE_DIR:?}/requirements.txt"

    # Check if the virtual environment directory exists
    if [[ ! -d "$venv_path" ]]; then
        echo "shared_shell_history: Creating virtual environment..."
        if ! python3 -m venv "$venv_path"; then
            echo "shared_shell_history: Failed to create virtual environment." >&2
            return 1
        fi

        # Activate the virtual environment
        source "$venv_path/bin/activate"

        echo "shared_shell_history: Installing dependencies..."
        if ! pip install -r "$requirements_path"; then
            echo "shared_shell_history: Failed to install dependencies." >&2

            # Deactivate and remove the virtual environment
            deactivate
            echo "shared_shell_history: Removing virtual environment..."
            rm -rf "$venv_path"
            return 1
	else
	    # Deactivate the virtual environment
            deactivate
        fi
    fi

    # Run the Python command with arguments
    "${venv_path}/bin/python" "$@"

    local python_exit_status=$?

    # Return the exit status of the Python command
    return $python_exit_status
}
