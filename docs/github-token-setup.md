# GitHub Token Setup — Acceso de Claude a repositorios

## Objetivo

Configurar un Fine-grained Personal Access Token (PAT) para que Claude pueda
trabajar en tus repositorios de GitHub: crear ramas, pushear commits y abrir
Pull Requests — sin poder mergear directamente a la rama principal.

## Flujo de trabajo resultante

```
Claude → crea rama → pushea commits → abre PR → tú revisas → tú mergeas
```

Claude propone. Tú decides.

---

## 1. Crear el token en GitHub

Ve a:
```
GitHub → Settings → Developer settings → Personal access tokens
       → Fine-grained tokens → Generate new token
```

Configura:
- **Token name:** `claude-bot` (o el nombre que prefieras)
- **Expiration:** la que consideres (90 días recomendado, luego rotas)
- **Repository access:** All repositories (o solo los que quieras)

### Permisos necesarios

| Permiso | Nivel |
|---|---|
| Contents | Read and write |
| Pull requests | Read and write |
| Metadata | Read (obligatorio, viene por defecto) |

El resto en **No access**.

Haz clic en **Generate token** y copia el valor — solo se muestra una vez.

---

## 2. Proteger la rama principal

Para que Claude no pueda saltarse el proceso de PR y pushear directo a master:

```
Repo → Settings → Rules → Rulesets → New ruleset
```

Configura:
- **Ruleset name:** `protect-master`
- **Enforcement:** Active
- **Target branches:** Include default branch
- **Rules:** activa *Require a pull request before merging*

Guarda. A partir de aquí, cualquier push directo a master (incluso con el token)
será rechazado por GitHub.

---

## 3. Guardar el token en el contenedor

Dentro del contenedor de Claude:

```bash
mkdir -p ~/.secrets
echo "github_pat_XXXXXXXXXXXX" > ~/.secrets/github_token
chmod 600 ~/.secrets/github_token
```

Configura git para usarlo automáticamente:

```bash
TOKEN=$(cat ~/.secrets/github_token)
git config --global credential.helper store
git remote set-url origin "https://onyxdream:${TOKEN}@github.com/onyxdream/<repo>.git"
```

Configura la identidad de los commits:

```bash
git config --global user.name "Claude (onyxdream-bot)"
git config --global user.email "claude@onyxdream"
```

---

## 4. Verificar que funciona

```bash
# El token puede leer y escribir
TOKEN=$(cat ~/.secrets/github_token)
curl -s -H "Authorization: Bearer ${TOKEN}" \
  https://api.github.com/repos/onyxdream/<repo> | jq '.permissions'

# Debe mostrar push: true

# El push directo a master debe estar bloqueado
git commit --allow-empty -m "test"
git push origin master
# → remote: Changes must be made through a pull request.
```

---

## Consideraciones de seguridad

- El token nunca va en el repositorio. Siempre en `~/.secrets/` (fuera de cualquier repo).
- `~/.secrets/github_token` tiene permisos `600` — solo legible por tu usuario.
- Si sospechas que el token se ha comprometido, revócalo desde GitHub inmediatamente:
  `Settings → Developer settings → Fine-grained tokens → [token] → Delete`
- Rota el token periódicamente (cada 90 días es razonable).

---

## Rotar el token

1. Genera un nuevo token en GitHub con los mismos permisos
2. Actualiza el archivo en el contenedor:
   ```bash
   echo "github_pat_NUEVO" > ~/.secrets/github_token
   chmod 600 ~/.secrets/github_token
   TOKEN=$(cat ~/.secrets/github_token)
   git remote set-url origin "https://onyxdream:${TOKEN}@github.com/onyxdream/<repo>.git"
   ```
3. Revoca el token viejo en GitHub
