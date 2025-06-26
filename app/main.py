from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .core.database import engine, Base
from .api import auth, organizations, clusters, deployments

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    debug=settings.DEBUG
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
app.include_router(clusters.router, prefix="/clusters", tags=["clusters"])
app.include_router(deployments.router, prefix="/deployments", tags=["deployments"])

@app.get("/")
async def root():
    return {"message": "MLOps Platform API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 