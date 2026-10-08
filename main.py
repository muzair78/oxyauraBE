from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

import app.model.user  # noqa: F401 - Register models with Base
import app.model.reports  # noqa: F401 - Register models with Base
import app.model.document_chunks  # noqa: F401 - Register models with Base
import app.model.conversation  # noqa: F401 - Register models with Base
import app.model.healthReadings  # noqa: F401 - Register models with Base
from app.api.authentication import router as auth_router
from app.api.reports import router as reports_router
from app.api.userQueiries import router as chat_router
from app.api.healthReadings import router as health_readings_router
from app.db.connection import Base, connect_db, engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    if not await connect_db():
        raise RuntimeError("Database connection failed; server startup aborted")

    async with engine.begin() as conn:
        # Enable pgvector extension if not already enabled
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        # Create tables in database if they don't already exist
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables verified/created successfully!")

    yield

    await engine.dispose()


app = FastAPI(title="Doctor API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(reports_router)
app.include_router(chat_router)
app.include_router(health_readings_router)


@app.get("/")
def home():
    return {"message": "Hello FastAPI!"}