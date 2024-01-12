# Shared Shell History

## Introduction

`shared-shell-history` is a tool designed to enhance the command-line experience by enabling the sharing and synchronization of shell history across multiple systems. This utility is particularly useful for developers, system administrators, and any CLI users who work on multiple machines or sessions and wish to have a unified view of their command history.

Whether you're switching between local and remote sessions or working across different systems, `shared-shell-history` ensures that your command history is always at your fingertips. It's built with simplicity and efficiency in mind, allowing seamless integration into your existing workflow.

## Features

`shared-shell-history` offers a range of features designed to enhance your command-line efficiency across multiple environments:

- **Multi-System Synchronization**: Seamlessly sync your shell history across various systems, ensuring access to your command history no matter where you are.

- **Session Management**: Keep track of your command history in different sessions, whether you're on local or remote machines.

- **Efficient Search Functionality**: Quickly search through your integrated shell history to find specific commands.

- **User-Friendly Interface**: Enjoy a clean and intuitive interface for browsing and selecting commands from your history.

- **Easy Installation and Setup**: Get up and running with minimal setup, thanks to a straightforward installation process.

- **Cross-Platform Compatibility**: Designed to work seamlessly on various UNIX-like systems, including Linux and macOS.

- **Open Source**: Dive into the source code, customize it, and contribute to the development of `shared-shell-history`.

These features are geared towards making your command-line experience more productive and enjoyable, saving you time and effort in your day-to-day tasks.

## Installation

`shared-shell-history` is designed to enhance your Bash experience. Follow these steps to install it on your system:

### Prerequisites

Before installing, make sure you have:

- Python 3.6 or higher with venv support (Install `python3-venv` on Ubuntu)
- Bash shell, version 5.1 or higher recommended (lower versions might work but are not guaranteed)

### Database Setup (Optional)

`shared-shell-history` supports all databases compatible with SQLAlchemy. You can set up a database server of your choice (e.g., PostgreSQL, MySQL) and provide the database URI during installation. Tables are automatically created if they don't exist.

I suggest using sqlite for testing `shared-shell-history` and move to a database server if you like using `shared-shell-history`.
A sqlite database will automatically be created if you provide an sqlite-URI of the form `sqlite:////absolute/path/to/database.db`.
To learn more about the supported databases: [SQLAlchemy - Engine Configuration](https://docs.sqlalchemy.org/en/20/core/engines.html)


### Installing from Source

1. **Clone the Repository**:
   Clone `shared-shell-history` from GitHub:
   ```bash
   git clone https://github.com/ManuelWiese/shared-shell-history.git
   cd shared-shell-history
   ```
2. **Run the Installation Script**:
   Execute the installation script. You can optionally provide a database URI as a parameter; if not provided, you'll be prompted to enter one, with a default suggestion of `sqlite:///~/.shared_shell_history/history.db` This will set up `shared-shell-history` and modify your .bashrc file.:
   ```bash
   ./install.sh [database-uri]
   ```
3. **Reload Your Shell**:
   To apply the changes, reload your shell or:
   ```bash
   source ~/.bashrc
   ```

### Uninstalling
To uninstall `shared-shell-history`, navigate to the cloned repository directory, disable the command capture and run the `uninstall.sh` script. After that reload your shell.
```bash
cd path/to/cloned/shared-shell-history
shared_shell_history_disable_capture
./uninstall.sh
```

## Usage

`shared-shell-history` automatically synchronizes your command history to a database, making it accessible across sessions and systems. Here's how to effectively use it:

### Command Synchronization

- **Automatic Sync**: Every command you execute in the shell is added to the database before execution. This includes long-running commands and even those executed before unexpected system crashes.

### Enabling/Disabling Command Capture

- **Disable Capture**: If you wish to stop recording commands temporarily, you can disable command capture:
  ```bash
  shared_shell_history_disable_capture
  ```
- **Enable Capture**: To resume command recording, enable command capture:
  ```bash
  shared_shell_history_enable_capture
  ```

### Interactive Search Menu

- **Accessing the Menu**: Press **Ctrl+h** to open the interactive search menu.
- **Features**:
  - **Filter Commands**: You can filter the commands displayed in the menu by user, host and using regex strings.
  - **Command Info**: Selecting a command displays detailed information, such as the execution path, virtual environment (if any) and the timestamp when the command was added to the database.
- **Navigating the Menu**: Use the arrow keys to navigate through your command history in the menu.
- **Selecting a Command**: Press Enter to select and load a command into your current shell session.
- **Exiting the Menu**: Press 'q' to exit the menu and return to your shell.

### Tips for Effective Use

- **Cross-Session Accessibility**: Commands entered in one session are instantly available in all others where `shared-shell-history` is active.
- **Remote Sessions**: For remote terminals, install `shared-shell-history` on your remote machine to access your unified command history remotely.
