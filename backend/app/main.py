from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.models.database import init_db
from app.routers import digest, users, verification

settings = get_settings()

# Initialize database on startup
init_db()

app = FastAPI(
    title=settings.app_name,
    description="AI-powered stock advisory - daily top 5 buy/sell recommendations",
    version="0.1.0",
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(digest.router, prefix="/api/digest", tags=["digest"])
app.include_router(users.router, prefix="/api/user", tags=["users"])
app.include_router(verification.router, prefix="/api/verification", tags=["verification"])


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "app": settings.app_name}


@app.get("/")
async def root():
    return {
        "message": "Welcome to StockPulse AI",
        "docs": "/docs",
        "health": "/api/health",
    }
