# Infrastructure Principles

## Philosophy

All infrastructure is reproducible. Any new machine must be fully operational with:

```bash
git clone <repo>
./setup.sh
```

No manual steps, no configuration living only in someone's head.

## Repository organization

By functional domain, not by individual service.
If multiple containers belong to the same domain, they go in the same repo.

```
claude-docker/     ← development environment with Claude Code
homelab-ai/        ← local AI stack (Ollama, Open WebUI, agents...)
homelab-storage/   ← file server (future)
homelab-docs/      ← centralized documentation (future)
```

## Minimum structure for each repo

```
<project>/
├── setup.sh              ← install from scratch on a new machine
├── .env.example          ← required environment variables (no real values)
├── docker-compose.yml    ← service definitions
├── docs/                 ← decisions, design, notes
└── .github/
    └── workflows/        ← CI/CD
```

## Rules

- **IPs and environment-specific values** → always in `.env`, never hardcoded
- **Secrets** → never in the repo, referenced as environment variables
- **Desired state** → declared in the repo, not in anyone's head
- **Each service** → independent, can be added or removed without breaking others

## Environments

| Machine | Role | IP |
|---|---|---|
| Laptop | Development, Claude Code | dynamic (not critical) |
| Server (desktop) | Production services | fixed on local network (via .env) |
