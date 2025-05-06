import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from languages import languages
from utils import get_language_sources

# Load environment variables from .env file
load_dotenv()

# Now you can access your environment variables
MONGO_URI = os.getenv("MONGO_URI")
SECRET_KEY = os.getenv("SECRET_KEY")
# For debugging, to make sure the value is loaded
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
    language = language.lower() # This is what caused so many issues. It was saying Python vs python
    lang_sources = sources.get(language)
  
    # Logging for error
    if not lang_sources:
        raise HTTPException(status_code=404, detail="Language not found")
    
    url = lang_sources.get(topic) or lang_sources.get("default")
    if not url:
        raise HTTPException(status_code=404, detail="Documentation source not found")
    
    return {"url": url}

