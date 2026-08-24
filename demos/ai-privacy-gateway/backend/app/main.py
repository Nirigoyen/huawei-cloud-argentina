from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers.process import router as process_router

app = FastAPI(
    title="AI Privacy Gateway",
    description="Anonymizes PII before sending to LLM and reconstructs the response.",
    version="1.0.0",
)

cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(process_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
