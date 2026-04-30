# Principios de infraestructura

## Filosofía

Toda la infraestructura es reproducible. Cualquier máquina nueva debe quedar
operativa con:

```bash
git clone <repo>
./setup.sh
```

Sin pasos manuales adicionales, sin configuración en la cabeza del usuario.

## Organización de repositorios

Por dominio funcional, no por servicio individual.
Si varios contenedores forman parte del mismo dominio, van en el mismo repo.

```
claude-docker/     ← entorno de desarrollo con Claude Code
homelab-ai/        ← stack de IA local (Ollama, Open WebUI, agentes...)
homelab-storage/   ← servidor de ficheros (futuro)
homelab-docs/      ← documentación centralizada (futuro)
```

## Estructura mínima de cada repo

```
<proyecto>/
├── setup.sh              ← instalación desde cero en máquina nueva
├── .env.example          ← variables de entorno necesarias (sin valores reales)
├── docker-compose.yml    ← definición de servicios
├── docs/                 ← decisiones, diseño, notas
└── .github/
    └── workflows/        ← CI/CD
```

## Reglas

- **IPs y valores específicos del entorno** → siempre en `.env`, nunca hardcodeados
- **Secrets** → nunca en el repo, referenciados como variables de entorno
- **Estado deseado** → declarado en el repo, no en la cabeza de nadie
- **Cada servicio** → independiente, se puede añadir o quitar sin romper el resto

## Entornos

| Máquina | Rol | IP |
|---|---|---|
| Portátil | Desarrollo, Claude Code | dinámica (no crítica) |
| Servidor (sobremesa) | Servicios en producción | fija en red local (via .env) |
