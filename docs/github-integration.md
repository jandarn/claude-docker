# Optional: GitHub Integration

If you want Claude to interact with your GitHub repositories — creating branches,
pushing commits, and opening Pull Requests — you can configure a GitHub token
inside the container.

## How it works

Claude operates under a **minimal-permission model**:

```
Claude → creates branch → pushes commits → opens PR → you review → you merge
```

Claude proposes changes. You decide what gets merged.

---

## 1. Create a Fine-grained Personal Access Token

Go to:
```
GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens
```

Required permissions:

| Permission | Level |
|---|---|
| Contents | Read and write |
| Pull requests | Read and write |
| Metadata | Read (default) |

Leave everything else at **No access**.

---

## 2. Protect your main branch

Prevent any direct push to your main branch by requiring a PR:

```
Repo → Settings → Rules → Rulesets → New ruleset
```

- **Target:** Include default branch
- **Enable:** Require a pull request before merging

This ensures Claude can never bypass your review — even with write access,
all changes must go through a PR that only you can merge.

---

## 3. Store the token inside the container

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

> **Note:** The token is stored outside any repository directory and with
> restricted file permissions (`600`). Never commit it to a repo.

---

## 4. Rotate the token periodically

Tokens should be rotated every 90 days:

1. Generate a new token on GitHub with the same permissions
2. Update the file in the container:
   ```bash
   echo "github_pat_NEW_TOKEN" > ~/.secrets/github_token
   chmod 600 ~/.secrets/github_token
   ```
3. Revoke the old token on GitHub
