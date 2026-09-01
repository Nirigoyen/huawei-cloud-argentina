# CCI 3-Tier — Demo de Cloud Container Instance

Demo de Huawei CCI con una aplicación 3-tier real (frontend + backend + Redis) que muestra load balancing, service discovery y estado compartido en vivo desde una UI interactiva.

## Descripción

A diferencia de un demo que solo muestra la IP del contenedor con `whoami`, este demo muestra una arquitectura completa funcionando en CCI:

```
Internet → ELB → frontend-svc (LoadBalancer :80)
                    ↓
              frontend pods (nginx + UI, 2 réplicas)
                    ↓ proxy /api/ → backend-svc:8080
              backend pods (Flask API, 2 réplicas)
                    ↓ redis-svc:6379
              redis pod (1 réplica)
```

La UI muestra:
- **Contador de visitas** persistido en Redis (compartido entre todos los pods)
- **Log de requests** con timestamp + pod hostname + IP — al hacer click "Incrementar" se ven distintos pods del backend atendiendo (load balancing del service ClusterIP)
- **Info del backend** que cambia cada 3s (auto-poll) mostrando distintos pods
- **Diagrama de arquitectura** del flujo completo

## Prerrequisitos

### Local (docker-compose)
- Docker + Docker Compose

### CCI
- `kubectl` configurado para CCI
- Namespace `demo-cci` creado en CCI
- `imagePullSecret` configurado (`imagepull-secret`)
- Un ELB ID para el service LoadBalancer

## Quickstart local

```bash
make up
# Abrir http://localhost:8081
```

## Deploy en CCI

### 1. Build y push de imágenes

```bash
SWR=swr.la-south-2.myhuaweicloud.com

docker build --provenance=false -t $SWR/demo-cci/frontend:latest ./frontend
docker push $SWR/demo-cci/frontend:latest

docker build --provenance=false -t $SWR/demo-cci/backend:latest ./backend
docker push $SWR/demo-cci/backend:latest

docker pull redis:alpine
docker tag redis:alpine $SWR/demo-cci/redis:alpine
docker push $SWR/demo-cci/redis:alpine
```

> **Importante:** usar `--provenance=false` porque SWR no soporta manifest lists multi-arch de BuildKit.

### 2. Deployar manifests

Editar `cci/frontend.yaml` y reemplazar `<PEGAR_TU_ELB_ID_AQUI>` con el ELB ID real.

```bash
kubectl apply -f cci/redis.yaml
kubectl apply -f cci/backend.yaml
kubectl apply -f cci/frontend.yaml
```

### 3. Acceder

```bash
kubectl get svc demo-frontend-svc -n demo-cci
# Abrir la EXTERNAL-IP en el navegador
```

## Variables de entorno

| Variable | Descripción | Default |
|----------|-------------|---------|
| `REDIS_HOST` | Hostname de Redis (backend) | `localhost` |
| `MENSAJE_DEMO` | Mensaje mostrado en la UI | `¡Hola desde el backend en Huawei CCI!` |
| `BACKEND_HOST` | Hostname del backend (frontend nginx) | `backend-svc` |

## Arquitectura

| Componente | Imagen | Réplicas | Service |
|---|---|---|---|
| Frontend | `nginx:alpine` + UI + proxy | 2 | LoadBalancer :80 |
| Backend | `python:3.12-alpine` + Flask | 2 | ClusterIP :8080 |
| Redis | `redis:alpine` | 1 | ClusterIP :6379 |

Todos los pods usan `resource.cci.io/instance-type: general-computing` con limits de 250m CPU / 512Mi memory. Los deployments de frontend y backend tienen `podAntiAffinity` por zona para alta disponibilidad.

## Qué demuestra de CCI

| Feature | Cómo se ve |
|---|---|
| Multi-deployment | 3 deployments separados trabajando juntos |
| Service discovery | frontend → `backend-svc`, backend → `redis-svc` |
| Load balancing | Log de requests muestra pods distintos |
| Estado compartido | Contador persiste en Redis across pods |
| Tipos de service | LoadBalancer (frontend) + ClusterIP (backend, redis) |
| Env vars | `MENSAJE_DEMO` visible en la UI |
| Anti-affinity | Pods distribuidos across AZs |

## Estructura

```
cci-3tier/
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf.template   (envsubst: ${BACKEND_HOST})
│   └── index.html            (UI)
├── backend/
│   ├── Dockerfile
│   ├── app.py                (Flask API)
│   └── requirements.txt
├── cci/
│   ├── redis.yaml            (Deployment + Service)
│   ├── backend.yaml          (Deployment + Service)
│   └── frontend.yaml         (Deployment + LoadBalancer Service)
├── docker-compose.yml        (para correr local)
├── Makefile
└── .env.example
```
