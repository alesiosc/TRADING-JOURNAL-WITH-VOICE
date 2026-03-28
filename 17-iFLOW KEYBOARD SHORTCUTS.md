 # iFlow CLI Keyboard Shortcuts

  ## Navigation & Editing
  - ↑ / ↓ - Navigate command history
  - ← / → - Move cursor left/right
  - Tab - Auto-complete commands
  - Enter - Execute command
  - Backspace - Delete character before cursor
  - Delete - Delete character after cursor

  ## Text Editing
  - Ctrl + A - Move to beginning of line
  - Ctrl + E - Move to end of line
  - Ctrl + K - Delete from cursor to end of line
  - Ctrl + U - Delete from cursor to beginning of line
  - Ctrl + W - Delete word before cursor
  - Ctrl + Y - Paste last deleted text

  ## History & Search
  - Ctrl + R - Search command history
  - Ctrl + P - Previous command
  - Ctrl + N - Next command

  ## Session Control
  - Ctrl + C - Cancel current operation
  - Ctrl + D - Exit iFlow CLI
  - Ctrl + L - Clear screen
  - Ctrl + Z - Suspend iFlow CLI

  ## File Operations
  - Ctrl + O - Open file browser
  - Ctrl + S - Save session output

  ## Help
  - F1 - Show help documentation
  - Ctrl + H - Show command history

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

## Basics:                                                                                                                      │
│ Add context: Use @ to specify files for context (e.g., @src/myFile.ts) to target specific files or folders.                  │
│ Shell mode: Execute shell commands via ! (e.g., !npm run start) or use natural language (e.g. start server).                 │
│                                                                                                                              │
│ # Commands:                                                                                                                    │
│  /about - show version info                                                                                                  │
│  /language - change the language                                                                                             │
│    zh-CN - 简体中文                                                                                                          │
│    en-US - English                                                                                                           │
│  /agents - Commands for interacting with agents.                                                                             │
│    list - List available agents.                                                                                             │
│    refresh - Refresh agents from source files.                                                                               │
│    online - Browse and install agents from online repository                                                                 │
│    install - Install a new agent with guided setup                                                                           │
│  /auth - change the auth method                                                                                              │
│  /bug - submit a bug report                                                                                                  │
│  /chat - Manage conversation history.                                                                                        │
│    list - List saved conversation checkpoints                                                                                │
│    save - Save the current conversation as a checkpoint. Usage: /chat save <tag>                                             │
│    resume - Resume a conversation from a checkpoint. Usage: /chat resume <tag>                                               │
│    delete - Delete a conversation checkpoint. Usage: /chat delete <tag>                                                      │
│  /clear - clear the screen and conversation history                                                                          │
│  /commands - Manage marketplace commands: list local, browse online, get details, add/remove from CLI (project/global scope) │
│    list - List locally installed commands from project and global scopes                                                     │
│    online - Browse available commands from online marketplace in an interactive dialog                                       │
│    get - Get details about a specific command by ID                                                                          │
│    add - Add a specific command by ID to local CLI (use --scope global for system-wide install)                              │
│    remove - Remove a locally installed command (use --scope global to remove from global)                                    │
│  /compress - Compresses the context by replacing it with a summary. (aliases: /compact, /summarize)                          │
│  /copy - Copy the last result or code snippet to clipboard                                                                   │
│  /corgi - Toggles corgi mode.                                                                                                │
│  /demo - Interactive task for research and brainstorming workflows                                                           │
│  /docs - open full iFlow CLI documentation in your browser                                                                   │
│  /directory - Manage workspace directories                                                                                   │
│    add - Add directories to the workspace. Use comma to separate multiple paths                                              │
│    show - Show all directories in the workspace                                                                              │
│  /editor - set external editor preference                                                                                    │
│  /export - Export conversation history                                                                                       │
│    clipboard - Copy the conversation to your system clipboard                                                                │
│    file - Save the conversation to a file in the current directory                                                           │
│  /extensions - list active extensions                                                                                        │
│  /help - for help on iflow-cli                                                                                               │
│  /ide - manage IDE connection                                                                                                │
│  /init - Analyzes the project and creates or updates a tailored IFLOW.md file.                                               │
│  /log - show current session log storage location                                                                            │
│  /mcp - list configured MCP servers and tools, browse online repository, or authenticate with OAuth-enabled servers          │
│    list - Interactive list of configured MCP servers and tools                                                               │
│    auth - Authenticate with an OAuth-enabled MCP server                                                                      │
│    online - Browse and install MCP servers from online repository                                                            │
│    refresh - Refresh the list of MCP servers and tools, and reload settings files                                            │
│  /memory - Commands for interacting with memory.                                                                             │
│    show - Show the current memory contents.                                                                                  │
│    add - Add content to the memory.                                                                                          │
│    refresh - Refresh the memory from the source.                                                                             │
│  /model - change the model                                                                                                   │
│  /output-style - change your output style preferences (use --scope global for global settings)                               │
│  /output-style:new - use '/output-style:new <description>' to create a custom output style                                   │
│  /quit - exit the cli                                                                                                        │
│  /resume - Resume a previous conversation from history                                                                       │
│  /stats - check session stats. Usage: /stats [model|tools]                                                                   │
│    model - Display model usage statistics                                                                                    │
│    tools - Display tool usage statistics                                                                                     │
│  /theme - change the theme                                                                                                   │
│  /tools - list available iFlow CLI tools                                                                                     │
│  /vim - toggle vim mode on/off                                                                                               │
│  /setup-github - Set up GitHub Actions                                                                                       │
│  ! - shell command                                                                                                           │
│                                                                                                                              │
│ # Keyboard Shortcuts:                                                                                                          │
│ Alt+Left/Right - Jump through words in the input                                                                             │
│ Ctrl+C - Quit application                                                                                                    │
│ Ctrl+Enter - New line                                                                                                        │
│ Ctrl+L - Clear the screen                                                                                                    │
│ Ctrl+X - Open input in external editor                                                                                       │
│ Ctrl+Y - Toggle YOLO mode                                                                                                    │
│ Enter - Send message                                                                                                         │
│ Esc - Cancel operation                                                                                                       │
│ Shift+Tab / Alt+M - Toggle mode                                                                                              │
│ Up/Down - Cycle through your prompt history                                                                                  │
│                                                                                                                              │
│ `For a full list of shortcuts, see docs/keyboard-shortcuts.md`