"""
Helios Voters List Scraper
Scrapes public voter list pages from links_HELIOS.txt
and saves each page as XML.
"""

import requests
from bs4 import BeautifulSoup
import time
import os
import json
import re
from urllib.parse import urljoin, urlparse, parse_qs
import xml.etree.ElementTree as ET
from xml.dom import minidom


SCRAPER_SETTINGS = {
    "delay_between_requests": 2,  # Seconds between requests
    "output_directory": "data HELIOS",   # Directory to save XML files
    "separate_files": True       # Each topic to separate file
}

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"


class HeliosScraper:
    """
    Scraper for public Helios voter list pages.
    No authentication is required.
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        })

    def read_links_from_file(self, filename="links_HELIOS.txt"):
        """
        Read URLs from file.
        """
        if not os.path.exists(filename):
            print(f"❌ Error: {filename} file not found!")
            return []

        urls = []
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    urls.append(line)

        print(f"✓ Loaded {len(urls)} URLs.")
        return urls

    def extract_election_info_from_url(self, url):
        """
        Extract election_id and page number.
        Example:
        .../elections/<id>/voters/list?page=2
        """
        try:
            parsed = urlparse(url)
            parts = parsed.path.split("/")
            election_id = parts[3]
            query = parse_qs(parsed.query)
            page = query.get("page", ["1"])[0]
            return election_id, page
        except:
            return None, None

    def scrape_url(self, url):
        """
        Downloads page and returns structured info.
        """
        election_id, page = self.extract_election_info_from_url(url)
        if not election_id:
            print("❌ URL format not recognized")
            return None

        try:
            r = self.session.get(url)
            if r.status_code != 200:
                print(f"❌ Status {r.status_code}")
                return None
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return None

        return {
            "election_id": election_id,
            "page": page,
            "url": url,
            "raw_html": r.text,
            "scraped_at": time.strftime('%Y-%m-%d %H:%M:%S'),
            "status_code": r.status_code,
            "content_length": len(r.text)
        }

    def save_page_as_xml(self, page_data, output_dir="data_HELIOS"):
        """
        Saves the downloaded HTML page as XML file.
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        filename = f"election_{page_data['election_id']}_page_{page_data['page']}.xml"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(page_data['raw_html'])

        print(f"✓ Saved: {filepath}")
        return filepath

    def save_summary_xml(self, scraped_files, output_dir="data_HELIOS"):
        """
        Creates summary XML listing saved files.
        """
        root = ET.Element("scraping_summary")
        root.set("scraped_at", time.strftime('%Y-%m-%d %H:%M:%S'))
        root.set("total_pages", str(len(scraped_files)))

        for filepath, data in scraped_files:
            page = ET.SubElement(root, "page")
            page.set("election_id", data['election_id'])
            page.set("page", data['page'])
            page.set("file", os.path.basename(filepath))

        summary_file = os.path.join(
            output_dir,
            f"summary_{time.strftime('%Y%m%d_%H%M%S')}.xml"
        )

        rough = ET.tostring(root, 'utf-8')
        pretty = minidom.parseString(rough).toprettyxml(indent="  ")

        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(pretty)

        print(f"✓ Summary saved: {summary_file}")

    def run(self, links_file="links_HELIOS.txt"):
        print("=== Helios Voters List Scraper ===")
        print("ℹ Login skipped — public access assumed.\n")

        output_dir = SCRAPER_SETTINGS.get("output_directory", "data_HELIOS")
        urls = self.read_links_from_file(links_file)
        if not urls:
            return

        scraped_files = []
        print("🚀 Starting...\n")

        start = time.time()

        for base_url in urls:
            print(f"\n--- Processing election URL: {base_url} ---")

            # Generate pages 1–25
            for page_num in range(1, 26):
                # Replace or insert ?page=
                if "page=" in base_url:
                    url = re.sub(r"page=\d+", f"page={page_num}", base_url)
                else:
                    join_char = "&" if "?" in base_url else "?"
                    url = base_url + f"{join_char}page={page_num}"

                print(f"  → Fetching page {page_num}...", end=" ")

                data = self.scrape_url(url)

                # Stop if page does not exist or is empty
                if not data or data["content_length"] < 500:  # small pages = no data
                    print(" (no more pages, stopping)")
                    break

                filepath = self.save_page_as_xml(data, output_dir)
                scraped_files.append((filepath, data))
                print("✓")

                time.sleep(SCRAPER_SETTINGS.get("delay_between_requests", 1))

        if scraped_files:
            self.save_summary_xml(scraped_files, output_dir)

        print("\n✅ Done.")


def main():
    scraper = HeliosScraper()
    scraper.run("links_HELIOS.txt")


if __name__ == "__main__":
    main()
