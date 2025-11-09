# Pirate Forum Scraper

Advanced web scraper for the Pirate Party Forum (forum.pirati.cz) with automatic Keycloak SSO authentication and XML data extraction.

## Features

- **Automatic authentication** via Keycloak SSO system
- **Scraping of topics and posts** from forum.pirati.cz
- **XML data export** with detailed structure
- **Configurable topic ranges** for targeted scraping
- **Advanced topic existence detection** with debugging information
- **Rate limiting compliance** for gentle server load
- **Robust error handling** and detailed reporting
- **Support for both public and protected content**

## Project Structure

```text
pirates/
├── main.py              # Main scraper with Keycloak authentication
├── config.py            # Configuration for credentials and settings
├── requirements.txt     # Python dependencies
├── README.md           # Documentation
└── data/               # Output XML files and summary reports
```

## Installation

1. Install required packages:

```bash
pip install -r requirements.txt
```

2. Edit `config.py` and set:
   - USERNAME and PASSWORD (your forum credentials)
   - TARGET_URL (URL of specific topic for priority scraping)
   - Topic ID range in SCRAPER_SETTINGS
   - USER_AGENT as needed

## Usage

### Basic Usage

```bash
python main.py
```

The scraper automatically:

1. Loads configuration from `config.py`
2. Attempts to log in via Keycloak SSO
3. Generates topic range for scraping
4. Creates output directory
5. Progressively scrapes topics with progress reporting
6. Saves XML files and creates summary report

### Configuration

Edit `config.py` for customization:

```python
# Forum login credentials
USERNAME = "your_username"  # Your forum username
PASSWORD = "your_password"  # Your forum password

# Target URL for priority scraping
TARGET_URL = "https://forum.pirati.cz/viewtopic.php?t=47593"

# Scraper settings
SCRAPER_SETTINGS = {
    "delay_between_requests": 2,    # Seconds between requests (recommended 2+)
    "output_directory": "data",     # Directory for XML files
    "separate_files": True,         # Each topic to separate file
    "topic_id_range": {
        "start": 47590,             # Starting topic ID
        "end": 47595,               # Ending topic ID
        "step": 1                   # Step (usually 1)
    }
}

# User agent for HTTP requests
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36..."
```

## Output

The scraper creates an organized file structure:

### XML files for individual topics

- **`topic_[ID]_[title].xml`** - Each topic in a separate file
- **Contains**: complete topic data including all posts

### Summary files

- **`scraping_summary_[timestamp].xml`** - Overview of all successfully scraped topics
- **Progress reporting** during execution with statistics

### XML Output Structure

```xml
<topic id="47593" url="https://forum.pirati.cz/viewtopic.php?t=47593" scraped_at="2025-06-27 10:30:00">
    <title>CF 6/2019 Extraordinary Review - RP Resolution on New NDA</title>
    <posts count="10">
        <post id="p623124">
            <author>Martin.Kucera</author>
            <date>2019-06-14T20:58:55+00:00</date>
            <content>I hereby initiate proceedings of the national forum...</content>
        </post>
        <!-- additional posts -->
    </posts>
</topic>
```

## Technical Details

### Authentication

- **Keycloak SSO**: Automatic login via Keycloak system
- **Session management**: Maintains session throughout scraping process
- **Fallback**: Continues without login for public content

### Advanced Features

- **Intelligent topic existence detection**: Distinguishes between non-existent and empty topics
- **Forum structure parsing**: Optimized for phpBB3 forum structure
- **Error handling**: Robust error processing with detailed reporting
- **Rate limiting**: Configurable delays between requests

### Dependencies (requirements.txt)

```text
requests==2.31.0      # HTTP requests and session management
beautifulsoup4==4.12.2 # HTML parsing and data extraction
lxml==4.9.3           # Fast XML/HTML parser
```

## Notes and Tips

### Topic Range Configuration

- **Small range**: Use small range for testing (e.g., 5-10 topics)
- **Large range**: Set wider range for production scraping
- **Priority topic**: TARGET_URL topic will be processed first

### Performance and Ethics

- **Rate limiting**: Maintain at least 2 seconds between requests
- **Progress monitoring**: Progress report shown every 100 topics
- **Success rate**: Monitor scraping success rate in final report

### Security

- **Protect credentials**: Never commit passwords to public repositories
- **Environment variables**: Use environment variables for production
- **Responsible scraping**: Respect forum rules and don't overload server

## Troubleshooting

### Common Issues

**Login fails:**

- Check USERNAME and PASSWORD in config.py
- Verify account is not blocked
- Try logging in manually via browser

**Topics marked as non-existent:**

- Check topic_id_range - IDs might be too low/high
- Some topics may be deleted or inaccessible
- Verify you have access to relevant forum sections

**Slow scraping:**

- Only increase delay_between_requests if necessary
- Check internet connection
- Server may be rate limiting requests

### Debug Information

The scraper provides detailed information during execution:

- Login status and session management
- Progress reporting with time estimates
- Detailed error messages with troubleshooting guidance
- Success statistics at completion

## Warning

- **Use responsibly** and respect forum rules
- **Don't overload server** with excessive requests
- **Protect your credentials** - never commit them publicly
- **Follow rate limiting** - minimum 2 seconds between requests
- **Test with small ranges** before large-scale scraping
- **Monitor success rates** - low success rate may indicate issues

---

*This scraper is intended for research and archival purposes. Use responsibly and in accordance with the forum's Terms of Service.*
