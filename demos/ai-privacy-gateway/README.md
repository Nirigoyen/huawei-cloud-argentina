# AI Privacy Gateway

Demo de un gateway de privacidad que anonimiza información personal identificable (PII) antes de enviarla a un LLM y reconstruye la respuesta original.

## Descripción

Este demo muestra cómo proteger datos sensibles cuando se usa un LLM externo. El flujo es:

1. **Prompt original** → el usuario ingresa texto con datos sensibles (nombre, email, teléfono, DNI, tarjeta de crédito, dirección).
2. **Anonimización** → se detecta y reemplaza la PII con placeholders (`<PERSON_1>`, `<PHONE_NUMBER_1>`, etc.) usando [Presidio](https://microsoft.github.io/presidio/) + spaCy.
3. **LLM** → el prompt anonimizado se envía al LLM (compatible con API de OpenAI, ej: Huawei Cloud ModelArts MaaS).
4. **Reconstrucción** → la respuesta del LLM se deanomimiza reemplazando los placeholders por los valores originales.

Así, el LLM nunca recibe datos sensibles, pero el usuario ve la respuesta como si los hubiera enviado.

## Arquitectura

```
┌──────────┐     ┌──────────────────┐     ┌─────────┐     ┌──────────────────┐
│ Frontend │────▶│  Backend (FastAPI)│───▶│  LLM    │───▶│  Deanonimización │
│  React   │     │  Presidio + spaCy │     │  API    │     │  + Response      │
│  :8080   │     │  :8000            │     │         │     │                  │
└──────────┘     └──────────────────┘     └─────────┘     └──────────────────┘
```

- **Backend**: Python 3.12, FastAPI, Presidio (anonimización), spaCy (NLP en español e inglés), httpx (cliente HTTP).
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS. Muestra el pipeline de 4 pasos con cards animadas.
- **Docker**: docker-compose orquesta ambos servicios. El backend tiene un healthcheck en `/api/health`.

## Prerequisitos

- Docker + Docker Compose
- Una API key de un LLM compatible con la API de OpenAI (ej: Huawei Cloud ModelArts MaaS, OpenAI, etc.)

## Quickstart

1. Copiar el archivo de environment:

   ```bash
   cp .env.example .env
   ```

2. Editar `.env` con tu API key y URL del LLM.

3. Levantar el demo:

   ```bash
   make up
   ```

4. Abrir http://localhost:8080 en el navegador.

5. Ingresar un prompt con datos sensibles, por ejemplo:

   ```
   Mi nombre es Nicolas Garcia, mi email es nico@example.com y mi teléfono es +54 11 1234-5678.
   ¿Puedes confirmar mis datos?
   ```

6. Ver el pipeline de 4 pasos: prompt original, prompt anonimizado, respuesta del LLM, respuesta reconstruida.

## Variables de entorno

| Variable         | Descripción                          | Default                                           |
| ---------------- | ------------------------------------ | ------------------------------------------------- |
| `LLM_API_URL`    | URL del endpoint del LLM             | `https://api.openai.com/v1/chat/completions`      |
| `LLM_API_KEY`    | API key del LLM                      | `sk-placeholder`                                  |
| `LLM_MODEL_NAME` | Nombre del modelo a usar             | `gpt-4o-mini`                                     |
| `CORS_ORIGINS`   | Orígenes permitidos (separados por,) | `http://localhost,http://localhost:8080`          |

## Desarrollo local

### Backend

```bash
cd backend
pip install -e ".[dev]"
python -m spacy download es_core_news_md
python -m spacy download en_core_web_lg
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

El frontend corre en http://localhost:3000 con proxy a `/api` en el backend.

## Tests

```bash
cd backend
pytest
```

Los tests cubren las funciones puras del anonimizador (`detect_language` y `deanonymize_text`) y no requieren modelos de spaCy.

## Estructura del proyecto

```
ai-privacy-gateway/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + CORS + health
│   │   ├── config.py            # Settings (pydantic-settings)
│   │   ├── models.py            # Request/Response models
│   │   ├── routers/
│   │   │   └── process.py       # Endpoint /api/process_prompt
│   │   └── services/
│   │       ├── anonymizer.py    # Presidio + spaCy (anonimizar/deanonimizar)
│   │       └── llm_client.py    # Cliente HTTP del LLM
│   ├── tests/
│   │   └── test_anonymizer.py   # Tests de funciones puras
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── ruff.toml
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # Layout principal
│   │   ├── main.tsx             # Entry point
│   │   ├── types.ts             # Tipos TS
│   │   ├── components/
│   │   │   ├── PipelineCard.tsx # Card de cada step del pipeline
│   │   │   └── PromptInput.tsx  # Input + submit + grid de cards
│   │   └── services/
│   │       └── api.ts           # Cliente HTTP al backend
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── docker-compose.yml
├── Makefile
├── .env.example
└── README.md
```

## Comandos del Makefile

| Comando        | Descripción                              |
| -------------- | ---------------------------------------- |
| `make up`      | Levanta los contenedores (build + detach)|
| `make down`    | Detiene y elimina los contenedores       |
| `make logs`    | Muestra logs en tiempo real              |
| `make rebuild` | Fuerza rebuild y recreate                |
| `make clean`   | Detiene todo y elimina volúmenes e imágenes |
