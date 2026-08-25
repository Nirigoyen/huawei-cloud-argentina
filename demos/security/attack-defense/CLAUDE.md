# Attack & Defense Demo — Contexto para Agentes de IA

## Propósito

Demo de seguridad "Ataque y Defensa" con defense-in-depth. Un host corre DVWA con HSS+CES; un attacker corre sqlmap + SSH brute-force. Capas opcionales: CFW (perímetro) y WAF (L7).

## Destacado

Sin imagen custom — Ubuntu 24.04 pública + cloud-init. Todo (scripts, DVWA, virus files) vive en el repo.

## Estructura

- `main.tf` — provider, data source imagen, orchestración de módulos
- `vpc/` — 2 VPCs + subnets + security groups
- `ecs/` — host + attacker ECS, admin_pass (user/pass), EIPs, cloud-init
- `cfw/` — Cloud Firewall (opcional, `enable_cfw`)
- `waf/` + `dns/` — WAF + DNS CNAME (opcional, `enable_waf`)
- `cloud-init/` — host.yaml.tpl (Docker+DVWA+EICAR), attacker.yaml.tpl (sqlmap+paramiko+bruteforce)
- `scripts/` — ssh_bruteforce.py, run_demo.md

## Comandos

```bash
cp terraform.tfvars.example terraform.tfvars  # editar creds
make apply    # desplegar
make destroy  # destruir
```

## Reglas para agentes

1. No commitear secrets — `terraform.tfvars` está gitignored.
2. CFW/WAF son recursos paid — default `false`.
3. SGs usan `huaweicloud_networking_secgroup` (region-scoped, no VPC-scoped en este provider).
4. La imagen se resuelve via `huaweicloud_images_images` data source — no hardcodear UUIDs.
