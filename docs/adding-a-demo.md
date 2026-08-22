# Cómo Agregar un Demo

Guía paso a paso para agregar un nuevo demo al repositorio. Existen dos tipos de demos: **IaC** (infraestructura como código) y **de producto** (software). Ambos son autocontenidos.

## Tipos de Demos

### Tipo 1: Demos IaC (Terraform / Ansible)

Demos de infraestructura como código que provisionan recursos en la nube.

#### Ubicación

- **Terraform**: `demos/iac/terraform/<name>/`
- **Ansible**: `demos/iac/ansible/<name>/`

#### Pasos para Terraform

1. **Crear el directorio**:

```bash
mkdir -p demos/iac/terraform/<name>
```

2. **Agregar `README.md`**:

```markdown
# <Name del Demo> — Terraform

## Descripción
Qué infraestructura provisiona este demo.

## Prerrequisitos
- Terraform >= 1.5
- Credenciales de Huawei Cloud (AK/SK)

## Uso
\`\`\`bash
cp terraform.tfvars.example terraform.tfvars
# Editar terraform.tfvars
terraform init
terraform plan
terraform apply
\`\`\`

## Variables
| Variable | Descripción | Tipo | Default |
|----------|-------------|------|---------|
| region | Región de Huawei Cloud | string | us-east-1 |
| ... | ... | ... | ... |

## Limpieza
\`\`\`bash
terraform destroy
\`\`\`
```

3. **Agregar `variables.tf`** con todas las variables de entrada:

```hcl
variable "region" {
  description = "Región de Huawei Cloud"
  type        = string
  default     = "us-east-1"
}
```

4. **Agregar `terraform.tfvars.example`** (sin secretos reales):

```hcl
region = "us-east-1"
access_key = "your-ak-here"
secret_key = "your-sk-here"
```

5. **Agregar `Makefile` o script de ejecución**:

```makefile
.PHONY: init plan apply destroy

init:
	terraform init

plan:
	terraform plan

apply:
	terraform apply -auto-approve

destroy:
	terraform destroy -auto-approve
```

#### Pasos para Ansible

1. **Crear el directorio**:

```bash
mkdir -p demos/iac/ansible/<name>
```

2. **Agregar `README.md`** (misma estructura que Terraform pero con comandos `ansible-playbook`).

3. **Agregar `vars.yml`** con las variables del playbook:

```yaml
---
target_hosts: all
region: us-east-1
instance_type: s6.medium.1
```

4. **Agregar `inventory.yml`** o ejemplo de inventario:

```yaml
all:
  hosts:
    target:
      ansible_host: your-host-here
      ansible_user: root
```

5. **Agregar `Makefile` o script de ejecución**:

```makefile
.PHONY: check deploy

check:
	ansible-playbook -i inventory.yml playbook.yml --check

deploy:
	ansible-playbook -i inventory.yml playbook.yml
```

#### Plantilla IaC (Terraform)

```
demos/iac/terraform/<name>/
├── README.md
├── main.tf
├── variables.tf
├── outputs.tf
├── terraform.tfvars.example
├── Makefile
└── modules/
    └── <module>/
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

#### Plantilla IaC (Ansible)

```
demos/iac/ansible/<name>/
├── README.md
├── playbook.yml
├── vars.yml
├── inventory.yml
├── Makefile
└── roles/
    └── <role>/
        ├── tasks/
        │   └── main.yml
        ├── handlers/
        │   └── main.yml
        └── templates/
```

---

### Tipo 2: Demos de Producto (Software)

Demos de software que muestran capacidades de producto. Siguen las mismas reglas de autocontención que los workshops.

#### Ubicación

`demos/<name>/`

#### Pasos

1. **Crear el directorio**:

```bash
mkdir -p demos/<name>
```

2. **Agregar `README.md`** con descripción, prerrequisitos, quickstart (docker compose), variables de entorno y arquitectura.

3. **Agregar `CLAUDE.md`** con contexto del agente específico del demo.

4. **Agregar `docker-compose.yml`** si usa contenedores (con healthchecks para bases de datos).

5. **Agregar `.env.example`** con todas las variables requeridas, sin secretos reales.

6. **Agregar `Makefile`** con targets `up/down/logs/rebuild/clean`.

7. **Seguir convenciones de código** (ver `docs/conventions.md`).

8. **Agregar tests** en `tests/`.

9. **Actualizar el índice** `demos/README.md` si existe.

10. **Commit**:

```bash
git add demos/<name>
git commit -m "feat: agregar demo <name>"
```

#### Plantilla Demo de Producto

```
demos/<name>/
├── README.md
├── CLAUDE.md
├── docker-compose.yml
├── .env.example
├── Makefile
├── .gitignore
├── src/
│   ├── index.ts
│   └── config.ts
├── tests/
│   └── index.test.ts
└── package.json
```

## Checklist Final

### Para demos IaC
- [ ] Directorio en la ubicación correcta (`demos/iac/terraform/<name>/` o `demos/iac/ansible/<name>/`)
- [ ] README con descripción, prerrequisitos y uso
- [ ] Archivo de variables (`variables.tf` / `vars.yml`)
- [ ] Archivo de variables de ejemplo sin secretos
- [ ] Makefile o script de ejecución
- [ ] Commit con mensaje convencional

### Para demos de producto
- [ ] Directorio en `demos/<name>/`
- [ ] README con todas las secciones
- [ ] CLAUDE.md con contexto del agente
- [ ] docker-compose.yml con healthchecks
- [ ] .env.example sin secretos reales
- [ ] Makefile con targets up/down/logs/rebuild/clean
- [ ] Código pasa linting
- [ ] Tests pasan
- [ ] Commit con mensaje convencional
