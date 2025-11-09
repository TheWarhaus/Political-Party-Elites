#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pirate Forum Scraper with Authentication - URL List Version
Scrapes data from forum.pirati.cz based on URLs from links.txt file
"""
import requests
from bs4 import BeautifulSoup
import time
import os
import re
import json
from urllib.parse import urljoin, urlparse, parse_qs
import xml.etree.ElementTree as ET
from xml.dom import minidom
from config import SCRAPER_SETTINGS, USERNAME, PASSWORD, USER_AGENT

class PirateForumScraper:
    """
    A web scraper for the Pirate Forum (forum.pirati.cz) that handles authentication
    and extracts forum topics and posts into XML format from a list of URLs.
    
    This scraper can:
    - Authenticate via Keycloak SSO
    - Read URLs from links.txt file
    - Extract forum topics and posts
    - Save data in XML format with custom naming
    - Handle multiple pages of the same topic
    """
    
    def __init__(self):
        """
        Initialize the scraper with session configuration and headers.
        Sets up the requests session with appropriate headers for forum access.
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,cs;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.base_url = "https://forum.pirati.cz"
        self.login_url = "https://forum.pirati.cz/ucp.php?mode=login&redirect=index.php"
        
    def login(self, username, password):
        """
        Authenticate to the forum using Keycloak SSO.
        
        Args:
            username (str): Forum username
            password (str): Forum password
            
        Returns:
            bool: True if login successful, False otherwise
        """
        print(f"Attempting to log in as {username}...")
        
        # Load login page
        try:
            response = self.session.get(self.login_url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error loading login page: {e}")
            return False
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find Keycloak login form
        login_form = soup.select_one('form[id="kc-form-login"]')
        if not login_form:
            print("Error: Keycloak login form not found")
            return False
            
        # Get URL for submitting credentials
        action_url = urljoin(response.url, login_form.get('action'))
        
        # Extract hidden fields from form
        hidden_fields = {}
        for input_tag in login_form.find_all('input', type='hidden'):
            name = input_tag.get('name')
            value = input_tag.get('value', '')
            if name:
                hidden_fields[name] = value
                print(f"Hidden field: {name} = {value}")
        
        # Prepare login data
        login_data = {
            'username': username,
            'password': password,
        }
        login_data.update(hidden_fields)
        
        print(f"Submitting to: {action_url}")
        
        # Submit credentials to Keycloak
        try:
            response = self.session.post(action_url, data=login_data, allow_redirects=True)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error submitting credentials: {e}")
            return False
            
        print(f"Response: {response.status_code}, URL: {response.url}")
        
        # Test actual access to protected content
        print("Testing access to protected topic...")
        test_url = "https://forum.pirati.cz/viewtopic.php?t=47593"
        test_response = self.session.get(test_url)
        
        # Check if we can see protected content
        if "requires you to be registered and logged in" in test_response.text or "požaduje, abyste byli registrováni a přihlášeni" in test_response.text:
            print("✗ Login failed - still seeing registration required message")
            return False
        elif "Logout" in test_response.text or "Odhlásit se" in test_response.text:
            print("✓ Login successful!")
            return True
        else:
            # Try main page
            main_response = self.session.get("https://forum.pirati.cz/index.php")
            if "Logout" in main_response.text or "Odhlásit se" in main_response.text:
                print("✓ Login successful (verified on main page)!")
                return True
            else:
                print("✗ Login failed")
                return False

    def read_links_from_file(self, filename="links.txt"):
        """
        Read URLs from links.txt file.
        
        Args:
            filename (str): Path to the file containing URLs
            
        Returns:
            list: List of URLs to scrape
        """
        if not os.path.exists(filename):
            print(f"Error: {filename} file not found!")
            return []
        
        urls = []
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line and not line.startswith('#'):  # Skip empty lines and comments
                        if 'forum.pirati.cz' in line and 'viewtopic.php' in line:
                            urls.append(line)
                        else:
                            print(f"Warning: Line {line_num} doesn't look like a valid forum URL: {line}")
            
            print(f"✓ Read {len(urls)} URLs from {filename}")
            return urls
            
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            return []

    def extract_topic_info_from_url(self, url):
        """
        Extract topic ID and start parameter from URL.
        
        Args:
            url (str): Forum URL
            
        Returns:
            tuple: (topic_id, start_value) or (None, None) if extraction fails
        """
        try:
            # Parse URL
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            
            # Extract topic ID
            topic_id = None
            if 't' in query_params:
                topic_id = query_params['t'][0]
            
            # Extract start parameter (defaults to 0 if not present)
            start_value = "0"
            if 'start' in query_params:
                start_value = query_params['start'][0]
            
            return topic_id, start_value
            
        except Exception as e:
            print(f"Error parsing URL {url}: {e}")
            return None, None

    def scrape_url(self, url):
        """
        Download raw HTML content from a specific forum URL.
        
        Args:
            url (str): The URL to scrape
            
        Returns:
            dict or None: Data with raw HTML content or None if URL is invalid
        """
        try:
            response = self.session.get(url)
            if response.status_code != 200:
                return None
            
            # Check if we got a valid response with some content
            if len(response.text.strip()) < 100:  # Too short to be a real page
                return None
            
            # Quick check for obvious error pages
            response_text_lower = response.text.lower()
            error_indicators = [
                "this topic does not exist",
                "toto téma neexistuje",
                "topic not found",
                "téma nenalezeno",
                "page not found",
                "stránka nenalezena"
            ]
            
            # If we find obvious error messages, skip
            for indicator in error_indicators:
                if indicator in response_text_lower:
                    return None
            
            # Extract topic ID and start from URL
            topic_id, start_value = self.extract_topic_info_from_url(url)
            
            # Create data structure with raw HTML
            page_data = {
                'id': topic_id,
                'start': start_value,
                'url': url,
                'raw_html': response.text,
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'status_code': response.status_code,
                'content_length': len(response.text)
            }
            
            return page_data
            
        except Exception as e:
            print(f"Error scraping URL {url}: {e}")
            return None

    def save_page_as_html(self, page_data, output_dir="data"):
        """
        Save raw HTML content to a file with custom naming.
        
        Args:
            page_data (dict): Page data containing raw HTML content
            output_dir (str): Directory to save the HTML file
            
        Returns:
            str: Path to the saved HTML file
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Create filename with format: topic_id-site.html
        # where site is the start parameter value
        filename = f"topic_{page_data['id']}-{page_data['start']}.xml"
        filepath = os.path.join(output_dir, filename)
        
        # Save raw HTML to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(page_data['raw_html'])
        
        content_size_kb = page_data['content_length'] / 1024
        print(f"✓ Topic {page_data['id']} (start={page_data['start']}) saved to {filepath} ({content_size_kb:.1f} KB)")
        return filepath

    def save_summary_xml(self, scraped_files, output_dir="data"):
        """
        Create a summary XML file with links to individual HTML files.
        
        Args:
            scraped_files (list): List of tuples (filepath, page_data)
            output_dir (str): Directory to save the summary file
            
        Returns:
            str: Path to the saved summary XML file
        """
        root = ET.Element("forum_scraping_summary")
        root.set("scraped_at", time.strftime('%Y-%m-%d %H:%M:%S'))
        root.set("total_pages", str(len(scraped_files)))
        
        for filepath, page_data in scraped_files:
            page_elem = ET.SubElement(root, "page_file")
            page_elem.set("id", str(page_data['id']))
            page_elem.set("start", str(page_data['start']))
            page_elem.set("file", os.path.basename(filepath))
            page_elem.set("content_length", str(page_data['content_length']))
            page_elem.set("status_code", str(page_data['status_code']))
            
            url_elem = ET.SubElement(page_elem, "url")
            url_elem.text = page_data['url']
            
            scraped_elem = ET.SubElement(page_elem, "scraped_at")
            scraped_elem.text = page_data['scraped_at']
        
        # Format XML
        rough_string = ET.tostring(root, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        
        summary_file = os.path.join(output_dir, f"scraping_summary_{time.strftime('%Y%m%d_%H%M%S')}.xml")
        
        # Save to file
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(reparsed.toprettyxml(indent="  "))
        
        print(f"✓ Summary file saved to {summary_file}")
        return summary_file

    def run(self, username, password, links_file="links.txt"):
        """
        Main method to run the forum scraper with URLs from file.
        
        Args:
            username (str): Forum username for authentication
            password (str): Forum password for authentication
            links_file (str): Path to file containing URLs to scrape
        """
        print("=== Pirate Forum Scraper - URL List Mode ===")
        
        # Create output directory
        output_dir = SCRAPER_SETTINGS.get("output_directory", "data")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"✓ Created output directory: {output_dir}")
        
        # Login
        if not self.login(username, password):
            print("⚠ Continuing without login (public content only)")
        
        # Read URLs from file
        urls = self.read_links_from_file(links_file)
        if not urls:
            print("❌ No valid URLs found in links.txt file!")
            return
        
        print(f"Total {len(urls)} URLs to scrape")
        
        # Scrape URLs
        scraped_files = []
        successful_scrapes = 0
        skipped_urls = 0
        
        print(f"\n🚀 Starting scraping...")
        start_time = time.time()
        
        for i, url in enumerate(urls, 1):
            print(f"[{i}/{len(urls)}] Downloading {url}...", end=" ")
            
            page_data = self.scrape_url(url)
            if page_data:
                # Save raw HTML to file
                filepath = self.save_page_as_html(page_data, output_dir)
                scraped_files.append((filepath, page_data))
                
                successful_scrapes += 1
            else:
                skipped_urls += 1
                print("- failed to download or invalid page")
            
            # Progress every 10 URLs
            if i % 10 == 0:
                elapsed = time.time() - start_time
                remaining = (len(urls) - i) * (elapsed / i)
                print(f"\n📊 Progress: {i}/{len(urls)} ({i/len(urls)*100:.1f}%)")
                print(f"⏱ Time: {elapsed/60:.1f}min, remaining ~{remaining/60:.1f}min")
                print(f"✅ Successful: {successful_scrapes}, ❌ Skipped: {skipped_urls}\n")
            
            # Pause between requests
            delay = SCRAPER_SETTINGS.get("delay_between_requests", 2)
            time.sleep(delay)
        
        # Create summary file
        if scraped_files:
            self.save_summary_xml(scraped_files, output_dir)
            
            total_time = time.time() - start_time
            print(f"\n🎉 Scraping completed!")
            print(f"⏱ Total time: {total_time/60:.1f} minutes")
            print(f"✅ Successfully scraped: {successful_scrapes} URLs")
            print(f"❌ Skipped: {skipped_urls} URLs")
            print(f"📁 Files saved in directory: {output_dir}")
            print(f"📈 Success rate: {successful_scrapes/(successful_scrapes+skipped_urls)*100:.1f}%")
        else:
            print("\n⚠ No data was scraped")
            print("Possible reasons:")
            print("  - URLs in links.txt do not exist or are invalid")
            print("  - You don't have permission to access these URLs")
            print("  - Forum structure has changed")
            print(f"\nPlease check your {links_file} file and ensure URLs are correct.")

def main():
    """
    Main function to initialize and run the forum scraper.
    """
    # Use credentials from configuration
    username = USERNAME
    password = PASSWORD
    
    if not username or not password:
        # Fallback - ask for credentials if not in configuration
        username = input("Enter username: ").strip()
        password = input("Enter password: ").strip()
        
        if not username or not password:
            print("You must enter both username and password!")
            return
    
    print(f"Using credentials for user: {username}")
    
    # Initialize scraper
    scraper = PirateForumScraper()
    
    try:
        scraper.run(username, password, "links.txt")
    except KeyboardInterrupt:
        print("\n\nScraping interrupted by user")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()