# the goal is to load from language_sources - opens, reads, and return data as python
# 
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def get_language_sources():
    """Load language source URLs from the JSON file"""
    file_path = Path(__file__).parent / "language_sources.json"
    logger.info(f"Loading language sources from: {file_path}")

    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"JSON decoding failed: {e}")
        raise
# ran http://127.0.0.1:8000/docs-source?language=Python&topic=default
# returned {"url":"https://docs.python.org/3/"}