from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import get_settings
from app.websocket.sse import router as sse_router

settings = get_settings()

app = FastAPI(
    title="SurgiFlow API",
    description="Real-Time Surgical Supply Chain Intelligence",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(sse_router)


@app.get("/")
def root():
    return {
        "name": "SurgiFlow",
        "tagline": "Real-Time Surgical Supply Chain Intelligence",
        "docs": "/docs",
    }
