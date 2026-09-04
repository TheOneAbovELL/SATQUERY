from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(
    title="SatQuery AI",
    description="Backend API for SatQuery AI Platform",
    version="0.1.0"
)

app.include_router(router, prefix="/api/v1")

@app.get("/health")
def health_check():
    return {"status": "healthy"}
