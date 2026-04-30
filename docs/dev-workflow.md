# Dev Workflow — Diseño y decisiones

## Objetivo

Crear un entorno de desarrollo donde Claude propone cambios via PR y el usuario
decide qué entra en producción. Simple ahora, escalable después.

## Arquitectura actual

```
[Portátil]
  └── contenedor claude-docker
        └── Claude Code  ←  aquí trabajamos

[Servidor (sobremesa)]
  └── Docker instalado
  └── proyectos en ejecución
```

## Flujo de trabajo

```
1. Usuario pide un cambio a Claude
2. Claude crea una rama (feat/*, fix/*, etc.)
3. Claude pushea la rama y abre un PR en GitHub
4. Usuario revisa el PR en GitHub
5. Usuario hace merge si está de acuerdo
6. (futuro) GitHub Actions despliega automáticamente en el servidor
```

## Decisiones tomadas

| Decisión | Elección | Motivo |
|---|---|---|
| Git hosting | GitHub | Ya en uso, simple, Actions incluido |
| Self-hosted runner | Pendiente | Servidor con Docker disponible |
| Autenticación Claude | Fine-grained PAT | Permisos mínimos, revocable |
| Branch protection | Ruleset en master | Obliga PR, Claude no puede mergear |
| Futuro Git hosting | Forgejo (cuando escale) | Control total, compatible con GH Actions |

## Permisos del token (Fine-grained PAT)

- **Contents:** Read and write — pushear ramas y commits
- **Pull requests:** Read and write — abrir y comentar PRs
- **Metadata:** Read — obligatorio
- **Merge:** NO — bloqueado por Ruleset, solo el owner puede

## Próximos pasos

- [ ] Montar self-hosted runner en el servidor (contenedor Docker)
- [ ] Primer workflow de GitHub Actions para claude-docker
- [ ] Servidor de documentación (Wiki.js o similar) con backup/restore sencillo
