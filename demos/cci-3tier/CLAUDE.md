# CCI 3-Tier Demo

## Contexto

Demo de Huawei CCI (Cloud Container Instance) con app 3-tier: frontend nginx +
backend Flask + Redis. Muestra load balancing, service discovery, y estado
compartido en vivo desde una UI interactiva.

## Estructura

- `frontend/` — nginx con UI HTML/JS + proxy al backend vía envsubst (`${BACKEND_HOST}`)
- `backend/` — Flask API con contador en Redis (`/api/health`, `/api/info`, `/api/visit`, `/api/visits`)
- `cci/` — manifests de CCI (apiVersion `cci/v2`, namespace `demo-cci`)
- `docker-compose.yml` — para correr local sin CCI

## Imágenes SWR

Namespace: `demo-cci` en `swr.la-south-2.myhuaweicloud.com`

- `demo-cci/frontend:latest`
- `demo-cci/backend:latest`
- `demo-cci/redis:alpine`

## Build

SWR no soporta manifest lists multi-arch. Siempre buildear con:

```bash
docker build --provenance=false -t <tag> .
```

## Endpoints del backend

- `GET /api/health` — health check
- `GET /api/info` — pod hostname, IP, mensaje, estado Redis
- `POST /api/visit` — incrementa contador en Redis, devuelve count + pod info
- `GET /api/visits` — contador actual
