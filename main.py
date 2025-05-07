import os
import logging
from datetime import datetime
from bson.objectid import ObjectId
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Body, Path, Request, Depends, Header
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from pydantic import BaseModel, Field
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from languages import languages
from utils import get_language_sources

# Load environment variables from .env
load_dotenv()

# Setup logging / debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# From .env
MONGO_URI = os.getenv("MONGO_URI")
SECRET_KEY = os.getenv("SECRET_KEY")

app = FastAPI(
    title="Language Tutor API",
    description="An API to manage language tutoring sessions and documentation sources.",
    version="1.0.0"
)

# CORS setup – allow all for now, lock it down later
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API key check using header
def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != SECRET_KEY:
        raise HTTPException(status_code=401, detail="API key is missing or invalid.")

# Error handler for general exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Something went wrong on our end. Please try again later."},
    )

# Error handler for validation issues 
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content={"detail": "Invalid input. Please check the data you're sending and try again.", "errors": exc.errors()}
    )

# Models
class DocRequest(BaseModel):
    language: str = Field(..., description="The programming language (e.g., python, javascript)")
    topic: str = Field(default="default", description="The specific topic within the language")

class SessionRequest(BaseModel):
    user_id: str = Field(..., description="Unique identifier for the user")
    language: str = Field(..., description="Language the user is learning")
    topic: str = Field(default="default", description="Topic selected for the session")

# Ping for supported languages
@app.get("/languages", summary="Get supported languages", response_description="List of supported languages")
def get_languages(_: None = Depends(verify_api_key)):
    logger.debug("Fetching supported languages")
    return {"languages": languages}

# Get docs URL based on language and topic
@app.post("/docs-source", summary="Get documentation URL")
def get_doc_source(data: DocRequest = Body(...), _: None = Depends(verify_api_key)):
    logger.debug(f"Received data: {data.dict()}")
    sources = get_language_sources()
    lang_sources = sources.get(data.language.lower())

    if not lang_sources:
        logger.warning(f"Language {data.language} not found")
        raise HTTPException(status_code=404, detail=f"No documentation found for '{data.language}'.")

    url = lang_sources.get(data.topic) or lang_sources.get("default")

    if not url:
        logger.warning(f"No documentation found for topic {data.topic}")
        raise HTTPException(status_code=404, detail=f"No documentation found for topic '{data.topic}'.")

    logger.info(f"Returning docs URL: {url}")
    return {"url": url}

# Health check (pings Mongo)
@app.get("/health", summary="Health check")
def health_check(_: None = Depends(verify_api_key)):
    logger.debug("Health check: checking MongoDB connection")
    if not MONGO_URI:
        raise HTTPException(status_code=500, detail="Missing MongoDB URI in environment configuration.")

    try:
        mongo_client.admin.command("ping")
    except ConnectionFailure as e:
        logger.error(f"Mongo ping failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Database connection failed. Please try again later.")

    logger.info("MongoDB connection successful")
    return {"status": "healthy"}

# Save a user session to Mongo
@app.post("/session", summary="Create a learning session")
def create_session(data: SessionRequest = Body(...), _: None = Depends(verify_api_key)):
    try:
        logger.debug(f"Creating session for user {data.user_id} in {data.language} with topic {data.topic}")

        db = mongo_client["lang_tutor"]
        sessions = db["sessions"]

        session_data = {
            "user_id": data.user_id,
            "language": data.language.lower(),
            "topic": data.topic,
            "timestamp": datetime.utcnow()
        }

        result = sessions.insert_one(session_data)

        logger.info(f"Session created successfully with ID: {result.inserted_id}")

        return {
            "session_id": str(result.inserted_id),
            "message": f"Your session was created successfully! Session ID: {result.inserted_id}.",
            "details": "You can now continue learning the topic you've selected. Keep track of your sessions for better progress."
        }
    except Exception as e:
        logger.error(f"Error creating session for user {data.user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while creating your session. Please try again.")

# Get session by ID
@app.get("/session/{session_id}", summary="Get session by ID")
def get_session_by_id(session_id: str = Path(...), _: None = Depends(verify_api_key)):
    logger.debug(f"Fetching session by ID: {session_id}")

    db = mongo_client["lang_tutor"]
    sessions = db["sessions"]
    session = sessions.find_one({"_id": ObjectId(session_id)})

    if not session:
        logger.warning(f"Session with ID {session_id} not found")
        raise HTTPException(status_code=404, detail="We couldn't find that session. Please check the ID and try again.")

    session["_id"] = str(session["_id"])
    logger.info(f"Returning session: {session}")
    return session

# Get all sessions for a user
@app.get("/sessions/{user_id}", summary="Get all sessions for a user")
def get_sessions_for_user(user_id: str, _: None = Depends(verify_api_key)):
    logger.debug(f"Fetching sessions for user {user_id}")

    db = mongo_client["lang_tutor"]
    sessions = db["sessions"]
    user_sessions = list(sessions.find({"user_id": user_id}))

    for session in user_sessions:
        session["_id"] = str(session["_id"])

    logger.info(f"Found {len(user_sessions)} sessions for user {user_id}")
    return {"sessions": user_sessions}

# MongoDB startup/shutdown
@app.on_event("startup")
def startup_db_client():
    global mongo_client
    logger.debug("Starting up MongoDB client")
    mongo_client = MongoClient(MONGO_URI)

@app.on_event("shutdown")
def shutdown_db_client():
    logger.debug("Shutting down MongoDB client")
    mongo_client.close()
