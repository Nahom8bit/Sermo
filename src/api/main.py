from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

app = FastAPI(
    title="Telegram Bot API",
    description="API for managing Telegram bot with LLM integration",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.get("/")
async def root():
    return {"message": "Telegram Bot API is running"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "database": "ok",
            "redis": "ok",
            "ollama": "ok"
        }
    }

# Import and include routers
# from .routers import bot, chat, admin
# app.include_router(bot.router)
# app.include_router(chat.router)
# app.include_router(admin.router) 