# Dev Workflow — Design and decisions

## Goal

Create a development environment where Claude proposes changes via PR and the
user decides what gets merged into production. Simple now, scalable later.

## Current architecture

```
[Laptop]
  └── claude-docker container
        └── Claude Code  ←  we work here

[Server (desktop)]
  └── Docker installed
  └── running projects
```

## Workflow

```
1. User asks Claude for a change
2. Claude creates a branch (feat/*, fix/*, docs/*, etc.)
3. Claude pushes the branch and opens a PR on GitHub
4. User reviews the PR on GitHub
5. User merges if satisfied
6. (future) GitHub Actions automatically deploys to the server
```

## Decisions made

| Decision | Choice | Reason |
|---|---|---|
| Git hosting | GitHub | Already in use, simple, Actions included |
| Self-hosted runner | Pending | Server with Docker available |
| Claude auth | Fine-grained PAT | Minimal permissions, revocable |
| Branch protection | Ruleset on master | Requires PR, Claude cannot merge |
| Future Git hosting | Forgejo (when scaling) | Full control, GH Actions compatible |

## Token permissions (Fine-grained PAT)

- **Contents:** Read and write — push branches and commits
- **Pull requests:** Read and write — open and comment on PRs
- **Metadata:** Read — mandatory
- **Merge:** NO — blocked by Ruleset, only the owner can merge

## Next steps

- [ ] Set up self-hosted runner on the server (Docker container)
- [ ] First GitHub Actions workflow for claude-docker
- [ ] Documentation server (Wiki.js or similar) with simple backup/restore
