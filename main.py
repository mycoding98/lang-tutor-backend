import os
import requests
import logging
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from languages import languages
from utils import get_language_sources
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from pydantic import BaseModel

class DocRequest(BaseModel):
    language: str
    topic: str = "default"


# Load environment variables from .env file
load_dotenv()

# Basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Now you can access your environment variables
MONGO_URI = os.getenv("MONGO_URI")
SECRET_KEY = os.getenv("SECRET_KEY")
# For debugging, to make sure the value is loaded
print(f"Mongo URI: {MONGO_URI}")

app = FastAPI()

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # can restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/languages")
def get_languages():
    return {"languages": languages}

from fastapi import Body

@app.post("/docs-source")
def get_doc_source(data: DocRequest = Body(...)):
    sources = get_language_sources()
    language = data.language.lower()
    topic = data.topic
    lang_sources = sources.get(language)

    if not lang_sources:
        raise HTTPException(status_code=404, detail="Language not found")

    url = lang_sources.get(topic) or lang_sources.get("default")
    if not url:
        raise HTTPException(status_code=404, detail="Documentation source not found")

    return {"url": url}


@app.get("/health")
async def health_check():
    # Ensure Mongo URI is set
    if not MONGO_URI:
        raise HTTPException(status_code=500, detail="MONGO_URI is not set")

    # Attempt to connect and ping the MongoDB server
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        client.admin.command("ping")
    except ConnectionFailure as e:
        raise HTTPException(status_code=500, detail=f"MongoDB connection failed: {str(e)}")

    return {"status": "healthy"}

# User session saved to MongoDB
from datetime import datetime
from fastapi import Body
from bson.objectid import ObjectId

class SessionRequest(BaseModel):
    language: str
    topic: str = "default"

@app.post("/session")
def create_session(data: SessionRequest = Body(...)):
    try:
        client = MongoClient(MONGO_URI)
        db = client["lang_tutor"]
        sessions = db["sessions"]

        session_data = {
            "language": data.language.lower(),
            "topic": data.topic,
            "timestamp": datetime.utcnow()
        }

        result = sessions.insert_one(session_data)
        session_id = str(result.inserted_id)

        return {"session_id": session_id, "message": "Session created"}
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(status_code=500, detail="Could not create session")
