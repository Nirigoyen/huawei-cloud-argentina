# Guía de Despliegue

Guía paso a paso para desplegar un workshop. Diseñada para que un agente de IA pueda seguirla de forma secuencial.

## Prerrequisitos

Verificar que el entorno tiene:

1. **Docker** + **docker-compose** (o `docker compose` plugin v2)
2. **Git**
3. **Endpoint LLM** compatible con OpenAI:
   - URL base (ej: `https://api.openai.com/v1`)
   - API key
   - Nombre del modelo (ej: `gpt-4o`)

Verificar Docker:

```bash
docker --version
docker compose version
```

Si alguno falla, instalar Docker antes de continuar.

## Paso 1: Clonar el repositorio

```bash
git clone https://github.com/<org>/huawei-cloud-argentina.git
cd huawei-cloud-argentina
```

## Paso 2: Navegar al directorio del workshop

```bash
cd workshops/<workshop-name>
```

Reemplazar `<workshop-name>` con el workshop a desplegar (ej: `chatbi-dashboards`).

## Paso 3: Configurar variables de entorno

Copiar el archivo de ejemplo y llenar los valores:

```bash
cp .env.example .env
```

Editar `.env` con los siguientes valores obligatorios:

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `OPENAI_BASE_URL` | URL del endpoint LLM | `https://api.openai.com/v1` |
| `OPENAI_API_KEY` | API key del LLM | `sk-...` |
| `OPENAI_MODEL` | Nombre del modelo | `gpt-4o` |
| `SESSION_SECRET` | Secreto de sesión | Generar con `openssl rand -hex 32` |

Generar el secreto de sesión:

```bash
openssl rand -hex 32
```

Copiar el resultado y pegarlo como valor de `SESSION_SECRET` en `.env`.

## Paso 4: Levantar los servicios

Usar Makefile:

```bash
make up
```

O equivalentemente con docker compose:

```bash
docker compose up -d --build
```

Esto construye las imágenes y levanta los contenedores en background.

## Paso 5: Esperar a que los contenedores estén healthy

Verificar el estado de los contenedores:

```bash
docker ps
```

Revisar la columna `STATUS`. Todos los contenedores deben mostrar `(healthy)`. Si alguno muestra `(health: starting)`, esperar y volver a verificar.

Para ver logs en caso de problemas:

```bash
make logs
# o
docker compose logs -f
```

## Paso 6: Verificar el backend

Hacer una petición al endpoint de health:

```bash
curl http://localhost:8000/health
```

Respuesta esperada:

```json
{"status":"ok"}
```

Si la respuesta no es `{"status":"ok"}`, revisar logs del backend:

```bash
docker compose logs <workshop-name>-app
```

## Paso 7: Verificar el frontend

Verificar que el frontend responde:

```bash
curl -o /dev/null -w "%{http_code}" http://localhost:8080
```

Respuesta esperada: `200`

Si la respuesta no es `200`, revisar logs del frontend y verificar que el contenedor esté healthy.

## Paso 8: Configuración específica para chatbi-dashboards

Si el workshop es `chatbi-dashboards`, realizar los siguientes pasos adicionales:

1. **Abrir la interfaz de administración** en el navegador:

   ```
   http://localhost:8080/admin
   ```

2. **Crear un workshop** desde la interfaz de admin.

3. **Conectar una fuente PostgreSQL** con los siguientes datos:

   | Campo | Valor |
   |-------|-------|
   | Host | `postgres` |
   | Port | `5432` |
   | Database | `scenario` |
   | User | `workshop` |
   | Password | `workshop` |

4. **Compartir el código del workshop** con los participantes. El código se genera al crear el workshop en la interfaz de admin.

## Paso 9: Troubleshooting

### Conflicto de puertos

**Síntoma**: Error `bind: address already in use` al levantar contenedores.

**Solución**:

1. Identificar qué proceso usa el puerto:

```bash
sudo lsof -i :8000
sudo lsof -i :8080
```

2. Detener el proceso o cambiar el mapeo de puertos en `docker-compose.yml`.

3. Alternativamente, detener contenedores previos:

```bash
docker compose down
make clean
```

### El contenedor no inicia

**Síntoma**: El contenedor aparece como `Exited` o reinicia constantemente.

**Solución**:

1. Revisar logs:

```bash
docker compose logs <service-name>
```

2. Verificar que `.env` tenga todas las variables requeridas (comparar con `.env.example`).
3. Reconstruir la imagen desde cero:

```bash
make rebuild
make up
```

### La base de datos no se inicializa

**Síntoma**: El contenedor de Postgres está healthy pero las tablas no existen.

**Solución**:

1. Verificar que el volumen no tenga datos stale:

```bash
make clean
```

2. Levantar nuevamente:

```bash
make up
```

3. Conectarse a la BD y verificar:

```bash
docker exec -it <workshop-name>-postgres psql -U workshop -d scenario -c "\dt"
```

### Wren build falla

**Síntoma**: El servicio de Wren no completa el build o devuelve errores.

**Solución**:

1. Verificar que `OPENAI_BASE_URL`, `OPENAI_API_KEY` y `OPENAI_MODEL` sean válidos en `.env`.
2. Probar el endpoint LLM directamente:

```bash
curl -X POST ${OPENAI_BASE_URL}/chat/completions \
  -H "Authorization: Bearer ${OPENAI_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"model":"'"${OPENAI_MODEL}"'","messages":[{"role":"user","content":"hello"}]}'
```

3. Si el endpoint responde correctamente, reiniciar el servicio de Wren:

```bash
docker compose restart <wren-service>
```

4. Si persiste, reconstruir todo:

```bash
make clean
make rebuild
make up
```

## Resumen de Comandos

```bash
# Clonar y entrar
git clone https://github.com/<org>/huawei-cloud-argentina.git
cd huawei-cloud-argentina/workshops/<workshop-name>

# Configurar
cp .env.example .env
# Editar .env con los valores correctos
# SESSION_SECRET=$(openssl rand -hex 32)

# Levantar
make up

# Verificar
docker ps
curl http://localhost:8000/health
curl -o /dev/null -w "%{http_code}" http://localhost:8080

# Si todo está OK, abrir http://localhost:8080

# Detener
make down
```
