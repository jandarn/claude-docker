# 🛡️ Private Claude Code Environment

A secure, isolated Docker environment to run Claude Code (Anthropic's CLI tool) privately. This project ensures the AI only has access to explicitly shared files, protecting the rest of your host operating system.

---

## 🎯 Main Objectives

- **Security Isolation**:
  - No root access: Process runs under the `claude` user (dynamic UID/GID).
  - Limited access: Only read/write permissions on the /home/claude directory and its own configuration. Cannot access `/home`, `/etc`, or the host system.
- **Smart Automation**: A single script (`run.py`) manages the container lifecycle (auto-start if stopped) and launches the Claude Code session opening a shell on the host with Claude started automatically.

---

## 🏗️ Architecture

```mermaid
graph TD
    Host["Host System (Your PC)"] -->|"Shared Volumes"| Container["Docker Container (Ubuntu 24.04)"]
    Container -->|"User: claude (Non-Root)"| ClaudeCode["Claude Code CLI"]

    subgraph Security
        Container -.->|"No access to"| HostSystem["Rest of Host System"]
        Container -.->|"No privileges"| RootPriv["Root Privileges"]
    end

    runpy["run.py"] -->|"Orchestration"| Docker["Docker Engine"]
    Docker -->|"Start if necessary"| Container
```

---

## 📁 Project Structure

```
.
├── Dockerfile              # Base image: Ubuntu 24.04 + Node.js + Claude Code (user 'claude')
├── docker-compose.yml      # Service definition, volumes, and security restrictions
├── run.py                  # 🚀 Main script: Manages startup and execution
├── code-project/           # 📂 Shared directory (Your secure workspace)
├── .env                    # Environment variables (API KEY, etc.)
└── README.md               # Documentation
```

---

## 🚀 How It Works (`run.py`)

The `run.py` script is the single entry point. Its logic is:

1. **Check status**: Verifies if the `claude-code-dev` container is running.
2. **Auto-start**: If inactive, executes `docker-compose up -d` to launch it.
3. **Execution**: Injects the command to start the interactive Claude session inside the container.
4. **Error handling**: Detects if the API Key is missing or if the container failed to start.

---

### Expected Behavior

#### If container is stopped:

```bash
$ python run.py
🔍 Container not detected. Starting secure environment...
✅ Environment ready. Starting Claude Code session...
(claude@container) $ _
```

#### If container is already active:

```bash
$ python run.py
🔍 Container active. Connecting to existing session...
(claude@container) $ _
```

---

## 🔒 Security Measures Implemented

- **Non-Root User**: Container runs under the `claude` user (UID/GID mapped to host).
- **Restricted Volumes**:
  - Personal Claude directory: Change on .env file, mounts on /home/claude (container).
  - Rest of system: Inaccessible.

- **No Port Exposure**: Container does not expose ports to the host (internal communication only).
- **Limited Capabilities**: `no-new-privileges` and dropping unnecessary capabilities.

---

## 🛠️ Prerequisites

- Docker and Docker Compose installed.
- Python 3.8+ (for `run.py`).

---

## ⚙️ Configuration

### 1. Clone the repository

```bash
git clone git@github.com:onyxdream/claude-docker.git
cd claude-docker
```

### 2. Create an alias for `run.py` (Linux and Windows)

#### Linux (bash/zsh)

```bash
echo "alias claude-secure='python3 /absolute/path/to/claude-docker/run.py'" >> ~/.bashrc
source ~/.bashrc
```

For `zsh`, replace `~/.bashrc` with `~/.zshrc`.

#### Windows (PowerShell)

```powershell
if (!(Test-Path -Path $PROFILE)) { New-Item -ItemType File -Path $PROFILE -Force }
Add-Content $PROFILE "`nfunction claude-secure { python C:\absolute\path\to\claude-docker\run.py }"
. $PROFILE
```

After this, you can run `claude-secure` directly from your shell.

### 3. Run with python

```bash
python run.py
```

---
