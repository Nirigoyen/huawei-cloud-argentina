# Benchmarks

Tests de performance y benchmarks de Huawei Cloud Argentina.

## Cómo agregar un benchmark

1. Crear `benchmarks/<nombre>/`
2. Agregar `README.md` con: qué se mide, cómo correrlo, resultados esperados
3. Agregar el código del benchmark (script, docker-compose, etc.)
4. Agregar `.env.example` si necesita configuración
5. Commit con `feat: agregar benchmark <nombre>`

## Convenciones

- Cada benchmark es self-contained
- Resultados: documentar en el README del benchmark
- Usar formato reproducible (semillas, versiones fijas)
