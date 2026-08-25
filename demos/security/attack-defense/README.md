# Security Demo: Attack & Defense / Ataque y Defensa

[![Defense in Depth](https://img.shields.io/badge/defense-in-depth-blue.svg)]()

> Demo de seguridad con **defense-in-depth** para Huawei Cloud. Un host corre DVWA (Damn Vulnerable Web Application) con HSS + CES; un attacker lanza sqlmap + SSH brute-force. Capas opcionales: CFW (perímetro) y WAF (L7).
>
> *Security demo with **defense-in-depth** for Huawei Cloud. A host runs DVWA with HSS + CES; an attacker launches sqlmap + SSH brute-force. Optional layers: CFW (perimeter) and WAF (L7).*

---

## Español

### Destacado

**Sin imagen custom.** Usa Ubuntu 24.04 pública (resuelta por data source) + cloud-init que instala todo al boot. DVWA, scripts de ataque y archivos de virus (EICAR) viven en el repo — cualquier cliente clona y corre.

### Arquitectura

```
VPC host (10.0.0.0/16)                    VPC attacker (10.1.0.0/16)
┌──────────────────────────┐              ┌──────────────────────────┐
│  ECS host                │              │  ECS attacker            │
│  - Ubuntu 24.04          │              │  - Ubuntu 24.04          │
│  - DVWA (Docker)         │  ← ataques   │  - sqlmap                │
│  - HSS + CES (agent_list)│              │  - ssh_bruteforce.py     │
│  - EICAR virus files     │              │  - paramiko              │
│  - SG: 22, 80            │              │  - SG: 22                │
│  - EIP                   │              │  - EIP                   │
└──────────────────────────┘              └──────────────────────────┘
        │                                           │
        ├── [opcional] CFW (Cloud Firewall) ────────┤  IPS + ACL en el perímetro
        └── [opcional] WAF → DNS CNAME ─────────────┘  L7 + dominio
```

### Capas de defensa

| Capa | Toggle | Qué muestra | Costo |
|------|--------|-------------|-------|
| HSS + CES (host) | siempre on | virus scan (EICAR), vuln alerts, consumo de recursos | incluido en ECS |
| CFW (perímetro) | `enable_cfw` (default false) | IPS bloquea SQLi/brute-force, ACL granular | CFW Professional (paid) |
| WAF (L7 web) | `enable_waf` (default false) | bloqueo L7 del SQLi vía dominio | WAF postpaid (paid) |

Con todo off: demo mínimo (2 ECS, casi gratis). Prendiendo capas se arma defense-in-depth.

### Prerequisitos

- Terraform >= 1.5.0
- Credenciales de Huawei Cloud (AK/SK)
- Password de admin para las ECS (`ecs_password` — 8-32 chars, mayúsculas/minúsculas/números/especiales)
- Opcional: dominio propio en Huawei DNS (para WAF)

### Despliegue

```bash
cp terraform.tfvars.example terraform.tfvars
# Editar terraform.tfvars con tus credenciales y password de ECS
make apply
```

### Actividades del demo

1. **SSH al attacker** — `ssh root@<attacker_eip>` (ver output `ssh_to_attacker`)
2. **SSH brute-force** — `python3 /opt/ssh_bruteforce.py` (ver output `bruteforce_command`)
   - Esperado: todos los intentos fallan (el password del host es fuerte). HSS detecta los intentos.
3. **SQL injection** — `python3 /opt/sqlmap/sqlmap.py -u http://<host_eip>/vulnerabilities/sqli/?id=1 --dbs --level 3` (ver output `sqlmap_command`)
   - Sin WAF/CFW: sqlmap encuentra la inyección. Con WAF: bloqueado. Con CFW: IPS bloquea.
4. **Revisar consola Huawei** — HSS (virus EICAR, vulns), CES (métricas), CFW (attack logs), WAF (eventos L7)
5. **Cleanup** — `make destroy`

Ver `scripts/run_demo.md` para la guía paso a paso.

### Nota de costo

CFW Professional y WAF son recursos **opt-in paid** (`enable_cfw` y `enable_waf` default false). El demo mínimo (solo ECS) es casi gratis.

---

## English

### Highlight

**No custom image.** Uses public Ubuntu 24.04 (resolved via data source) + cloud-init that installs everything at boot. DVWA, attack scripts, and virus files (EICAR) live in the repo — any client clones and runs.

### Architecture

Two VPCs: a host VPC with an ECS running DVWA + HSS + CES, and an attacker VPC with an ECS running sqlmap + SSH brute-force. Optional CFW (perimeter IPS + ACL) and WAF (L7 protection + DNS) layers add defense-in-depth.

### Defense layers

| Layer | Toggle | What it shows | Cost |
|-------|--------|---------------|------|
| HSS + CES (host) | always on | virus scan (EICAR), vuln alerts, resource usage | included in ECS |
| CFW (perimeter) | `enable_cfw` (default false) | IPS blocks SQLi/brute-force, granular ACL | CFW Professional (paid) |
| WAF (L7 web) | `enable_waf` (default false) | L7 blocking of SQLi via domain | WAF postpaid (paid) |

With both off: minimal demo (2 ECS, near-free). Enabling layers builds defense-in-depth.

### Prerequisites

- Terraform >= 1.5.0
- Huawei Cloud credentials (AK/SK)
- Admin password for the ECS (`ecs_password` — 8-32 chars, upper/lower/digits/special)
- Optional: own domain in Huawei DNS (for WAF)

### Deploy

```bash
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your credentials and ECS password
make apply
```

### Demo activities

1. **SSH to attacker** — `ssh root@<attacker_eip>` (see output `ssh_to_attacker`)
2. **SSH brute-force** — `python3 /opt/ssh_bruteforce.py` (see output `bruteforce_command`)
   - Expected: all attempts fail (host password is strong). HSS detects the attempts.
3. **SQL injection** — `python3 /opt/sqlmap/sqlmap.py -u http://<host_eip>/vulnerabilities/sqli/?id=1 --dbs --level 3` (see output `sqlmap_command`)
   - Without WAF/CFW: sqlmap finds the injection. With WAF: blocked. With CFW: IPS blocks.
4. **Check Huawei console** — HSS (EICAR virus, vulns), CES (metrics), CFW (attack logs), WAF (L7 events)
5. **Cleanup** — `make destroy`

See `scripts/run_demo.md` for the step-by-step guide.

### Cost note

CFW Professional and WAF are **opt-in paid** resources (`enable_cfw` and `enable_waf` default false). The minimal demo (ECS only) is near-free.
