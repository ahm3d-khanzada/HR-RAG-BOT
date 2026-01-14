from fastapi import FastAPI
import logging

from auth.routes import router as auth_router
from docs.routes import router as docs_router
from chat.routes import router as chat_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI(
    title="HR Document & Query System API",
    description="Secure HR system with role-based access and RAG chat",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(docs_router, prefix="/docs", tags=["Documents"])
app.include_router(chat_router, prefix="/chat", tags=["HR Chat"])

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}