# Dify .env — generado por Terraform
# Metadata DB + vector store en RDS PostgreSQL (pgvector)
# El usuario admin de Huawei RDS PostgreSQL es "root" por defecto.

SECRET_KEY=${secret_key}
COMPOSE_PROFILES=pgvector,postgresql,collaboration

# Metadata DB -> RDS
DB_TYPE=postgresql
DB_HOST=${rds_host}
DB_PORT=5432
DB_USERNAME=root
DB_PASSWORD=${rds_password}
DB_DATABASE=dify
DB_PLUGIN_DATABASE=dify_plugin

# Vector store -> RDS pgvector
VECTOR_STORE=pgvector
PGVECTOR_HOST=${rds_host}
PGVECTOR_PORT=5432
PGVECTOR_USER=root
PGVECTOR_PASSWORD=${rds_password}
PGVECTOR_DATABASE=dify_vector

# Redis (containerizado, default de Dify)
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=difyai123456

# URLs publicas (EIP)
CONSOLE_API_URL=http://${dify_eip}
CONSOLE_WEB_URL=http://${dify_eip}
SERVICE_API_URL=http://${dify_eip}

# Plugin daemon
PLUGIN_DAEMON_KEY=${plugin_key}
