# Configuration for Pirate Forum Scraper

# Login credentials (SET YOUR OWN!)
# For security, we recommend using environment variables in production
USERNAME = "Filip.Vanco"
PASSWORD = "Heslonapiraty123"


# Scraper settings
SCRAPER_SETTINGS = {
    "delay_between_requests": 2,  # Seconds between requests
    "output_directory": "data",   # Directory to save XML files
    "separate_files": True       # Each topic to separate file
}

# User agent for HTTP requests
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
