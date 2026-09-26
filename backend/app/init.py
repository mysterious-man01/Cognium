from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import get_engine
from routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    get_engine()

    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    # Needed for custom headers in upload endpoint (GET)
    expose_headers=[
        "Attachment-Id",
        "File-Name"
    ]
)

app.include_router(router)
