# app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routers import ingest
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="GetGSA Document Parser",
    description="Parse company profiles and past performance documents",
    version="1.0.0"
)

# Mount static files for UI
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(ingest.router, prefix="/api", tags=["ingest"])

@app.get("/")
async def root():
    return {"message": "GetGSA Document Parser API"}
