#cloud-config
package_update: true
packages:
  - postgresql-client
  - git
  - curl

write_files:
  - path: /tmp/dify-env
    content: |
      ${env_content}

runcmd:
  # Install Docker (includes compose v2)
  - curl -fsSL https://get.docker.com | sh
  - systemctl enable --now docker
  # Clone Dify at the pinned version
  - git clone --depth 1 --branch ${dify_version} https://github.com/langgenius/dify.git /opt/dify
  # Place our .env overrides
  - cp /tmp/dify-env /opt/dify/docker/.env
  # Wait for RDS to be ready (up to ~10 min)
  - |
    for i in $(seq 1 60); do
      pg_isready -h ${rds_host} -p 5432 -U root && break
      echo "Waiting for RDS... ($$i/60)"
      sleep 10
    done
  # Create the vector database
  - PGPASSWORD='${rds_password}' psql -h ${rds_host} -U root -c "CREATE DATABASE dify_vector;" || true
  # Enable pgvector extension (Huawei RDS PostgreSQL 12+ supports it)
  - PGPASSWORD='${rds_password}' psql -h ${rds_host} -U root -d dify_vector -c "CREATE EXTENSION IF NOT EXISTS vector;" || PGPASSWORD='${rds_password}' psql -h ${rds_host} -U root -d dify_vector -c "SELECT control_extension('create', 'vector');"
  # Start Dify
  - cd /opt/dify/docker && docker compose up -d
