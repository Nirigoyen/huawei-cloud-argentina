# Guía de ejecución del demo / Demo run guide

Una vez que `make apply` termine, SSH al attacker y corré los ataques.

## 1. SSH al attacker / SSH to the attacker

```bash
ssh root@<attacker_eip>
```

## 2. SSH brute-force

```bash
python3 /opt/ssh_bruteforce.py
```

Intenta conexiones SSH al host con un diccionario chico de usuarios/passwords.
Esperado: todos fallan (el password del host es fuerte). Revisá HSS para ver los intentos.

## 3. SQL injection con sqlmap

```bash
python3 /opt/sqlmap/sqlmap.py -u http://<host_eip>/vulnerabilities/sqli/?id=1 --dbs --level 3
```

DVWA tiene SQLi por defecto. sqlmap debería encontrar la inyección y listar las DBs.
Si WAF está habilitado, los requests deberían ser bloqueados por WAF.
Si CFW está habilitado, el IPS debería bloquear los ataques en el perímetro.

## 4. Revisar la consola de Huawei Cloud / Check Huawei Cloud console

| Capa | Dónde / Where | Qué ver / What to see |
|------|--------------|----------------------|
| HSS  | Host Security Service | Virus alerts (EICAR), vulnerabilities, login attempts |
| CES  | Cloud Eye | CPU/memory/network metrics del host |
| CFW  | Cloud Firewall (si `enable_cfw`) | Attack logs, ACL hits, IPS blocks |
| WAF  | Web Application Firewall (si `enable_waf`) | L7 attack events, applied policies |

## 5. Cleanup

```bash
make destroy
```
