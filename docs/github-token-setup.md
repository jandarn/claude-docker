# GitHub Token Setup — Claude Access to Repositories

## Goal

Configure a Fine-grained Personal Access Token (PAT) so Claude can work on your
GitHub repositories: create branches, push commits, and open Pull Requests —
without being able to merge directly to the main branch.

## Resulting workflow

```
Claude → creates branch → pushes commits → opens PR → you review → you merge
```

Claude proposes. You decide.

---

## 1. Create the token on GitHub

Go to:
```
GitHub → Settings → Developer settings → Personal access tokens
       → Fine-grained tokens → Generate new token
```

Configure:
- **Token name:** `claude-bot` (or whatever you prefer)
- **Expiration:** your choice (90 days recommended, then rotate)
- **Repository access:** All repositories (or only the ones you want)

### Required permissions

| Permission | Level |
|---|---|
| Contents | Read and write |
| Pull requests | Read and write |
| Metadata | Read (mandatory, enabled by default) |

Leave everything else at **No access**.

Click **Generate token** and copy the value — it is only shown once.

---

## 2. Protect the main branch

To prevent Claude from bypassing the PR process and pushing directly to master:

```
Repo → Settings → Rules → Rulesets → New ruleset
```

Configure:
- **Ruleset name:** `protect-master`
- **Enforcement:** Active
- **Target branches:** Include default branch
- **Rules:** enable *Require a pull request before merging*

Save. From this point on, any direct push to master (even with the token)
will be rejected by GitHub.

---

## 3. Store the token in the container

Inside the Claude container:

```bash
mkdir -p ~/.secrets
echo "github_pat_XXXXXXXXXXXX" > ~/.secrets/github_token
chmod 600 ~/.secrets/github_token
```

Configure git to use it automatically:

```bash
TOKEN=$(cat ~/.secrets/github_token)
git config --global credential.helper store
git remote set-url origin "https://onyxdream:${TOKEN}@github.com/onyxdream/<repo>.git"
```

Set the commit identity:

```bash
git config --global user.name "Claude (onyxdream-bot)"
git config --global user.email "claude@onyxdream"
```

---

## 4. Verify it works

```bash
# The token can read and write
TOKEN=$(cat ~/.secrets/github_token)
curl -s -H "Authorization: Bearer ${TOKEN}" \
  https://api.github.com/repos/onyxdream/<repo> | jq '.permissions'

# Should show push: true

# Direct push to master must be blocked
git commit --allow-empty -m "test"
git push origin master
# → remote: Changes must be made through a pull request.
```

---

## Security considerations

- The token never goes in the repository. Always stored in `~/.secrets/` (outside any repo).
- `~/.secrets/github_token` has `600` permissions — readable only by your user.
- If you suspect the token has been compromised, revoke it immediately from GitHub:
  `Settings → Developer settings → Fine-grained tokens → [token] → Delete`
- Rotate the token periodically (every 90 days is reasonable).

---

## Rotating the token

1. Generate a new token on GitHub with the same permissions
2. Update the file in the container:
   ```bash
   echo "github_pat_NEW_TOKEN" > ~/.secrets/github_token
   chmod 600 ~/.secrets/github_token
   TOKEN=$(cat ~/.secrets/github_token)
   git remote set-url origin "https://onyxdream:${TOKEN}@github.com/onyxdream/<repo>.git"
   ```
3. Revoke the old token on GitHub
