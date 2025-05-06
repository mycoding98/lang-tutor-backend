import os
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from languages import languages
from utils import get_language_sources

# Load environment variables from .env file
load_dotenv()

# Access environment variables
MONGO_URI = os.getenv("MONGO_URI")
SECRET_KEY = os.getenv("SECRET_KEY")

# For debugging (you may remove this in production)
print(f"Mongo URI: {MONGO_URI}")

app = FastAPI()

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

@app.get("/docs-source")
def get_doc_source(language: str, topic: str = "default"):
    """Fetch the documentation URL for the given language/topic"""
    sources = get_language_sources()
    language = language.lower()  # This ensures case insensitivity
    
    lang_sources = sources.get(language)
  
    if not lang_sources:
        raise HTTPException(status_code=404, detail="Language not found")
    
    url = lang_sources.get(topic) or lang_sources.get("default")
    if not url:
        raise HTTPException(status_code=404, detail="Documentation source not found")
    
    return {"url": url}

@app.get("/health")
async def health_check():
    # 1. Check if MONGO_URI is available in environment variables
    if MONGO_URI is None:
        raise HTTPException(status_code=500, detail="MongoDB URI is not set")

    # 2. Check if SECRET_KEY is available in environment variables
    if SECRET_KEY is None:
        raise HTTPException(status_code=500, detail="SECRET_KEY environment variable is missing")

    # 3. Check external API service (optional, can be changed to relevant service)
    try:
        response = requests.get("https://some-external-service.com/status")
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="External service is down")
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=500, detail="External service is down")

    # If all checks pass
    return {"status": "healthy"}
