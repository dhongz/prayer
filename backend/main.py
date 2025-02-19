from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from app.config.config import config
from app.models import Base
from app.api import api_router

app = FastAPI(title="Prayer API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DATABASE_URL = config.DATABASE_URL
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(bind=engine)

# Import and include routers
# from backend.api.routes import router
# app.include_router(router)

@app.get("/")
async def root():
    return {"message": "Prayer API is running"}


app.include_router(api_router, prefix="/api/v1")