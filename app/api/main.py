from dotenv import load_dotenv
load_dotenv()
import os
os.environ["LANGSMITH_TRACING"] = os.getenv("LANGSMITH_TRACING", "fTRUE")
os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGSMITH_API_KEY", "")
os.environ["LANGSMITH_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "production-rag")
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
import os
from dotenv import load_dotenv
load_dotenv()

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")


app = FastAPI(
    title="Production RAG API",
    description="Document question answering with source citation, confidence scoring, and full observability.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "message": "Production RAG API is running.",
        "docs": "/docs",
        "health": "/api/v1/health",
    }