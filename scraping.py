import logging
import requests
from bs4 import BeautifulSoup

# Set up python logging configs
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# scrape MDN JavaScript pages
def scrape_mdn_js():
    url = "https://developer.mozilla.org/en-US/docs/Web/JavaScript"
    logger.debug(f"Attempting to fetch URL: {url}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        logger.debug(f"Successfully fetched URL: {url} with status code {response.status_code}")
    except requests.exceptions.HTTPError as e:
        logger.warning(f"HTTP error occurred: {e}")
        return None
    except requests.exceptions.RequestException as e:
        logger.critical(f"Network-related error fetching the page: {e}")
        return None
    
    soup = BeautifulSoup(response.content, 'html.parser')
    title = soup.title.string if soup.title else "No Title"
    logger.info(f"Page Title: {title}")
    return soup

# Function to chunk content (e.g., extract paragraphs and headers)
def chunk_content(soup):
    if not soup:
        logger.error("No soup to process!")
        return []
    
    paragraphs = soup.find_all('p')
    headers = soup.find_all(['h1', 'h2'])

    logger.debug(f"Found {len(headers)} headers and {len(paragraphs)} paragraphs.")
    
    chunks = []
    for header in headers:
        text = header.get_text().strip()
        if not text:
            logger.warning("Empty header found.")
        chunks.append(f"Header: {text}")
    
    for paragraph in paragraphs:
        text = paragraph.get_text().strip()
        if text:
            chunks.append(text)
        else:
            logger.warning("Empty paragraph found.")

    return chunks

# Clean chunks (text data)
def clean_data(chunks):
    cleaned = [chunk.strip() for chunk in chunks if chunk.strip()]
    logger.debug(f"Cleaned data contains {len(cleaned)} items.")
    return cleaned

# Save data to a file for progression
def save_scraped_data(data, filename="scraped_data.txt"):
    try:
        with open(filename, "w") as file:
            for item in data:
                file.write(item + "\n")
        logger.info(f"Data saved to {filename}")
    except Exception as e:
        logger.critical(f"Failed to save data to {filename}: {e}")

# Main testing
def main():
    logger.info("Starting scraping process...")
    soup = scrape_mdn_js()

    if soup:
        logger.info("Scraping completed. Chunking content...")
        chunks = chunk_content(soup)
        cleaned_chunks = clean_data(chunks)
        logger.info(f"Sample Chunks:\n{cleaned_chunks[:5]}")
        save_scraped_data(cleaned_chunks)
    else:
        logger.error("Scraping failed!")

if __name__ == "__main__":
    main()


# f-string. formatted string literal


# name = "Myah"     print(f"Hello, {name}!")
# Output: Hello, Myah!
# f"success"

