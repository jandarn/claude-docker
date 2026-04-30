# 🛡️ Private Claude Code Environment

A secure, isolated Docker environment to run Claude Code (Anthropic's CLI tool) privately. This project ensures the AI only has access to explicitly shared files, protecting the rest of your host operating system.

---

## 🎯 Main Objectives

- **Security Isolation**:
  - No root access: Process runs under the `claude` user (dynamic UID/GID).
  - Limited access: Only read/write permissions on the /home/claude directory and its own configuration. Cannot access `/home`, `/etc`, or the host system.
- **Admin Capabilities**: The `claude` user has `sudo` privileges without password prompt (safe in an isolated container environment) to install packages or modify the container as needed.
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

## � Admin Access for Container Modifications

The `claude` user has **passwordless sudo** access within the container, allowing Claude to install packages, modify configurations, or perform other administrative tasks when needed:

```bash
# Inside the container, Claude can run:
sudo apt update && sudo apt install -y some-package
sudo systemctl restart service-name
sudo nano /etc/some-config.conf
```

**Why passwordless?** The container is isolated from the host system. Granting sudo without password prompts allows Claude to work autonomously without requiring human intervention.

**⚠️ Note**: If you need a specific admin password for the container, you can:

1. Modify the Dockerfile to set a password during build
2. Manually inside the container: `sudo passwd claude` (then remove NOPASSWD from sudoers if preferred)

---

## �🛠️ Prerequisites

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

### 4. Run as root for troubleshooting

If you need to do troubleshooting work inside the container or install packages more easily, you can start an interactive root shell instead of launching Claude:

```bash
python3 run.py --root
```

This is useful for tasks such as:

- Installing packages with `apt`
- Inspecting or modifying system files inside the container
- Debugging container-level issues before returning to the normal Claude session

---

## 🐙 Optional: GitHub Integration

If you want Claude to interact with your GitHub repositories — creating branches,
pushing commits, and opening Pull Requests — you can configure a GitHub token
inside the container.

### How it works

Claude operates under a **minimal-permission model**:

```
Claude → creates branch → pushes commits → opens PR → you review → you merge
```

Claude proposes changes. You decide what gets merged.

### 1. Create a Fine-grained Personal Access Token

Go to `GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens`

Required permissions:

| Permission | Level |
|---|---|
| Contents | Read and write |
| Pull requests | Read and write |
| Metadata | Read (default) |

### 2. Protect your main branch

Prevent any direct push to your main branch by requiring a PR:

```
Repo → Settings → Rules → Rulesets → New ruleset
```

- Target: **Include default branch**
- Enable: **Require a pull request before merging**

This ensures Claude can never bypass your review — even with write access,
all changes must go through a PR that only you can merge.

### 3. Store the token inside the container

```bash
mkdir -p ~/.secrets
echo "github_pat_YOUR_TOKEN_HERE" > ~/.secrets/github_token
chmod 600 ~/.secrets/github_token

TOKEN=$(cat ~/.secrets/github_token)
git config --global credential.helper store
git config --global user.name "Claude (your-bot-name)"
git config --global user.email "claude@yourdomain"
git remote set-url origin "https://YOUR_USERNAME:${TOKEN}@github.com/YOUR_USERNAME/YOUR_REPO.git"
```

### 4. Rotate the token periodically

Tokens should be rotated every 90 days. Generate a new one on GitHub,
update `~/.secrets/github_token`, and revoke the old one.

> **Note:** The token is stored outside any repository directory and with
> restricted file permissions (`600`). Never commit it to a repo.
