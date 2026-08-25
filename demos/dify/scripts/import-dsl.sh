#!/usr/bin/env bash
# Importa un workflow DSL (YAML) a una instancia de Dify via console API.
#
# Uso:
#   ./import-dsl.sh <dify_url> <email> <password> <yaml_file>
#
# Ejemplo:
#   ./import-dsl.sh http://123.45.67.89 admin@example.com secret123 ../workflows/ejemplo-workflow.yaml
#
# Nota: el path primario para importar es via UI (crear app -> importar DSL).
#       Este script es una alternativa para automatizacion.
set -euo pipefail

if [ "$#" -ne 4 ]; then
  echo "Uso: $0 <dify_url> <email> <password> <yaml_file>"
  exit 1
fi

DIFY_URL="${1%/}"
EMAIL="$2"
PASSWORD="$3"
YAML_FILE="$4"

if [ ! -f "$YAML_FILE" ]; then
  echo "Error: no existe el archivo $YAML_FILE"
  exit 1
fi

# Login -> obtener access_token
LOGIN_RESP=$(curl -sS -X POST "${DIFY_URL}/console/api/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\"}")

TOKEN=$(echo "$LOGIN_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])" 2>/dev/null || echo "")

if [ -z "$TOKEN" ]; then
  echo "Error: no se pudo obtener el token de acceso. Respuesta del login:"
  echo "$LOGIN_RESP"
  exit 1
fi

echo "Token obtenido. Importando $YAML_FILE..."

# Construir el body JSON con el contenido del YAML y importar
BODY=$(python3 -c "import json; print(json.dumps({'mode':'yaml-content','yaml_content':open('${YAML_FILE}').read()}))")

IMPORT_RESP=$(curl -sS -X POST "${DIFY_URL}/console/api/apps/imports" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d "$BODY")

echo "Respuesta: $IMPORT_RESP"
