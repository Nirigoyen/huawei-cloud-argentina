# Dify on Huawei Cloud — Terraform

## Description

Self-hosted [Dify](https://github.com/langgenius/dify) deployment on Huawei Cloud using Terraform. Provisions:

- **ECS running Dify** (web app + API + worker) reachable via EIP.
- **ECS running Ollama** serving the `bge-m3` embeddings model (CPU-only, private in the VPC).
- **RDS PostgreSQL 15** with the **pgvector** extension — used as Dify's metadata DB and as the vector store for embeddings.
- **A new VPC** with subnet, security groups, and EIP.

## Architecture

```
VPC 10.0.0.0/16
├── Subnet 10.0.1.0/24
├── SG dify-sg      → ingress 80,443,22 from 0.0.0.0/0
├── SG ollama-sg    → ingress 11434 from 10.0.0.0/16, 22 from 0.0.0.0/0
├── SG rds-sg       → ingress 5432 from 10.0.0.0/16
├── EIP → dify-ecs
├── RDS PostgreSQL 15 (DBs: dify + dify_vector with pgvector)
├── ECS ollama-ecs (Ollama + bge-m3, private)
└── ECS dify-ecs (Dify docker compose, EIP)
```

Dify uses the RDS for metadata (DB `dify`) and as a vector store (DB `dify_vector` with pgvector). Redis stays containerized (Dify default). Ollama is reached via its private VPC IP — it has no EIP.

## Prerequisites

- Terraform >= 1.5
- Huawei Cloud credentials: Access Key (AK) and Secret Key (SK)
- An SSH public key (contents of `~/.ssh/id_rsa.pub`)
- Region `la-south-2` (Chile). The default flavors assume this region.

## Usage

```bash
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your credentials, SSH key, and RDS password
make init
make plan
make apply
```

Deployment takes ~10 minutes (the RDS is the slowest part). When done, `terraform output` shows:

```
dify_url          = http://<EIP>
ollama_private_ip = 10.0.1.x
ssh_dify          = ssh ubuntu@<EIP>
```

## Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `region` | Huawei Cloud region | `la-south-2` |
| `access_key` | Huawei Cloud AK | — |
| `secret_key` | Huawei Cloud SK | — |
| `ssh_public_key` | SSH public key | — |
| `availability_zone` | AZ within the region | `la-south-2a` |
| `dify_version` | Dify version (git tag) | `1.17.0` |
| `dify_flavor` | Dify ECS flavor | `s6.large.4` |
| `ollama_flavor` | Ollama ECS flavor | `s6.large.4` |
| `rds_flavor` | RDS flavor | `rds.pg.n1.large.2` |
| `rds_password` | RDS admin password | — |
| `eip_bandwidth` | EIP bandwidth (Mbit/s) | `5` |

## Post-deploy: configure models

Dify **cannot pre-configure model providers via environment variables** — this is done from the UI after deployment.

1. Open `terraform output -raw dify_url` in your browser.
2. Create the admin account (first access).
3. Go to **Settings → Model Provider → Ollama** (or **OpenAI-compatible** if native Ollama isn't listed).
4. Server URL: `http://<ollama_private_ip>:11434` (use the value from `terraform output -raw ollama_private_ip`).
5. Add the `bge-m3` model as type **Embedding**.
6. (Optional) Add an LLM (e.g. `qwen2.5`) if downloaded in Ollama.
7. When creating a Knowledge Base, select `bge-m3` as the embedding model.

## Import workflows

Workflow DSL YAML files go in [`workflows/`](workflows/). See [`workflows/README.md`](workflows/README.md) for the format and import options.

Quick import via UI: create app → **Import DSL** → upload the YAML.

Import via script:

```bash
./scripts/import-dsl.sh http://<EIP> admin@example.com password workflows/ejemplo-workflow.yaml
```

## Troubleshooting

### pgvector

Verify the extension is available on the RDS:

```bash
PGPASSWORD=<rds_password> psql -h <rds_private_ip> -U root -c \
  "SELECT * FROM pg_available_extension_versions WHERE name='vector';"
```

If it doesn't show up, upgrade the RDS minor version (Huawei RDS PostgreSQL 12+ supports pgvector on recent minor versions). The extension is enabled automatically during deployment via `CREATE EXTENSION IF NOT EXISTS vector`.

### SSH access

```bash
ssh ubuntu@<EIP>   # Dify ECS
```

Dify logs:

```bash
cd /opt/dify/docker && docker compose logs -f api
```

### RDS admin user

Huawei RDS PostgreSQL uses `root` as the default admin user. If your RDS uses a different user, edit `templates/dify-env.tpl` (`DB_USERNAME`, `PGVECTOR_USER`) and `templates/dify-cloud-init.yaml.tpl` (the `psql -U root` commands).

## Cleanup

```bash
make destroy
```

## Notes

- **No Ansible**: cloud-init provisions everything (Docker, Dify, Ollama, the pgvector extension). Ansible is not needed.
- Exact attribute names of the Huawei provider may vary between versions; `terraform validate` confirms them after `init`.
- The default flavors (`s6.large.4`, `rds.pg.n1.large.2`) may not exist in every region; override in `terraform.tfvars` if needed.
- The `db_postgres` and `pgvector` containers from Dify's docker-compose start but go unused (Dify points at the RDS). This is harmless and avoids `depends_on` issues.
