import os
import pandas as pd
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from datetime import datetime
import re
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ForumXMLParser:
    def __init__(self, input_folder="C:\\Users\\david\\OneDrive - Univerzita Karlova\\GAUK Michal\\parsing piratske forum\\data", output_folder="C:\\Users\\david\\OneDrive - Univerzita Karlova\\GAUK Michal\\parsing piratske forum\\data\\xlsx"):
        self.input_folder = input_folder
        self.output_folder = output_folder
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_folder, exist_ok=True)
    
    def clean_text(self, text):
        """Clean and normalize text content"""
        if not text:
            return ""
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        return text
    
    def parse_datetime(self, datetime_str):
        """Parse datetime string to standard format"""
        if not datetime_str:
            return ""
        
        try:
            # Handle various datetime formats
            if 'datetime=' in datetime_str:
                dt_match = re.search(r'datetime="([^"]+)"', datetime_str)
                if dt_match:
                    dt_str = dt_match.group(1)
                    # Parse ISO format datetime
                    dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                    return dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Try to extract date and time from text
            date_match = re.search(r'(\d{1,2}\s+\w+\s+\d{4}),?\s+(\d{1,2}:\d{2})', datetime_str)
            if date_match:
                return f"{date_match.group(1)} {date_match.group(2)}"
                
        except Exception as e:
            logger.warning(f"Failed to parse datetime: {datetime_str}, error: {e}")
        
        return datetime_str
    
    def extract_user_info(self, post_div):
        """Extract user information from post"""
        user_info = {}
        
        try:
            profile_div = post_div.find('dl', class_='postprofile')
            if profile_div:
                # Username
                username_link = profile_div.find('a', class_='username-coloured') or profile_div.find('a', class_='username')
                if username_link:
                    user_info['username'] = self.clean_text(username_link.get_text())
                    user_info['user_id'] = username_link.get('href', '').split('u=')[-1] if 'u=' in username_link.get('href', '') else ''
                
                # Profile rank
                rank_dd = profile_div.find('dd', class_='profile-rank')
                if rank_dd:
                    user_info['rank'] = self.clean_text(rank_dd.get_text())
                
                # Post count
                posts_dd = profile_div.find('dd', class_='profile-posts')
                if posts_dd:
                    posts_link = posts_dd.find('a')
                    if posts_link:
                        user_info['post_count'] = self.clean_text(posts_link.get_text())
                
                # Registration date
                joined_dd = profile_div.find('dd', class_='profile-joined')
                if joined_dd:
                    joined_text = joined_dd.get_text()
                    if 'Registrován:' in joined_text:
                        user_info['registration_date'] = self.clean_text(joined_text.replace('Registrován:', '').strip())
                
                # Profession
                profession_dd = profile_div.find('dd', class_='profile-custom-field profile-profese')
                if profession_dd:
                    profession_text = profession_dd.get_text()
                    if 'Profese:' in profession_text:
                        user_info['profession'] = self.clean_text(profession_text.replace('Profese:', '').strip())
                
                # Location
                location_dd = profile_div.find('dd', class_='profile-custom-field profile-phpbb_location')
                if location_dd:
                    location_text = location_dd.get_text()
                    if 'Bydliště:' in location_text:
                        user_info['location'] = self.clean_text(location_text.replace('Bydliště:', '').strip())
                
                # Thanks given and received
                thanks_given_dd = profile_div.find('dd', {'data-user-give-id': True})
                if thanks_given_dd:
                    thanks_link = thanks_given_dd.find('a')
                    if thanks_link:
                        thanks_text = thanks_link.get_text()
                        user_info['thanks_given'] = re.search(r'(\d+)', thanks_text).group(1) if re.search(r'(\d+)', thanks_text) else ''
                
                thanks_received_dd = profile_div.find('dd', {'data-user-receive-id': True})
                if thanks_received_dd:
                    thanks_link = thanks_received_dd.find('a')
                    if thanks_link:
                        thanks_text = thanks_link.get_text()
                        user_info['thanks_received'] = re.search(r'(\d+)', thanks_text).group(1) if re.search(r'(\d+)', thanks_text) else ''
        
        except Exception as e:
            logger.warning(f"Error extracting user info: {e}")
        
        return user_info
    
    def extract_post_content(self, post_div):
        """Extract post content and metadata"""
        post_data = {}
        
        try:
            # Post ID
            post_id = post_div.get('id', '').replace('p', '') if post_div.get('id') else ''
            post_data['post_id'] = post_id
            
            # Post title
            postbody_div = post_div.find('div', class_='postbody')
            if postbody_div:
                title_h3 = postbody_div.find('h3')
                if title_h3:
                    title_link = title_h3.find('a')
                    if title_link:
                        raw_title = self.clean_text(title_link.get_text())
                        post_data['title'] = raw_title.removeprefix("Re: ")
                
                # Post datetime
                author_p = postbody_div.find('p', class_='author')
                if author_p:
                    time_elem = author_p.find('time')
                    if time_elem:
                        post_data['datetime'] = self.parse_datetime(str(time_elem))
                
                # Post content
                content_div = postbody_div.find('div', class_='content')
                if content_div:
                    post_data['content'] = self.clean_text(content_div.get_text())
                
                # Thanks list
                thanks_dl = postbody_div.find('dl')
                if thanks_dl:
                    dt_elem = thanks_dl.find('dt')
                    if dt_elem and 'poděkovali autorovi' in dt_elem.get_text():
                        dt_text = dt_elem.get_text()
                        count_match = re.search(r'celkem (\d+)', dt_text)
                        if count_match:
                            post_data['thanks_count'] = int(count_match.group(1))
                        
                        dd_elem = thanks_dl.find('dd')
                        if dd_elem:
                            thanks_users = []
                            user_links = dd_elem.find_all('a', class_=['username-coloured', 'username'])
                            for link in user_links:
                                thanks_users.append(self.clean_text(link.get_text()))
                            post_data['thanks_users'] = ', '.join(thanks_users)

                            if 'thanks_count' not in post_data:
                                post_data['thanks_count'] = len(thanks_users)
                if 'thanks_users' not in post_data:
                    post_data['thanks_users'] = ''
                if 'thanks_count' not in post_data:
                    post_data['thanks_count'] = 0
                

        except Exception as e:
            logger.warning(f"Error extracting post content: {e}")
        
        return post_data
    
    def extract_forum_id_from_filename(self, filename):
        """Extract forum ID from filename like 'topic_38314-00.xml'"""
        try:
            # Extract the first number after 'topic_'
            match = re.search(r'topic_(\d+)', filename)
            if match:
                return match.group(1)
        except Exception as e:
            logger.warning(f"Could not extract forum ID from filename {filename}: {e}")
        return ""

    def parse_forum_xml(self, xml_content, forum_id=""):
        """Parse forum XML/HTML content and extract structured data"""
        soup = BeautifulSoup(xml_content, 'html.parser')
        posts_data = []
        
        # Find all post divs
        post_divs = soup.find_all('div', class_='post')
        
        if len(post_divs) == 0:
            logger.info(f"Found {len(post_divs)} posts to parse")
        
        for post_div in post_divs:
            try:
                # Extract user info
                user_info = self.extract_user_info(post_div)
                
                # Extract post content
                post_content = self.extract_post_content(post_div)
                
                # Combine user and post data
                post_data = {'forum_id': forum_id, **user_info, **post_content}
                posts_data.append(post_data)
                
            except Exception as e:
                logger.error(f"Error parsing post: {e}")
                continue
        
        return posts_data
    
    def create_xlsx_from_posts(self, posts_data, output_filename):
        """Create XLSX file from parsed posts data"""
        if not posts_data:
            logger.warning("No posts data to write")
            return
        
        # Create DataFrame
        df = pd.DataFrame(posts_data)
        
        # Ensure consistent column order
        columns = [
            'forum_id', 'post_id', 'title', 'username', 'user_id', 'rank', 'post_count',
            'registration_date', 'profession', 'location', 'thanks_given',
            'thanks_received', 'datetime', 'content',
            'thanks_users', 'thanks_count'
        ]
        
        # Reorder columns and fill missing ones
        for col in columns:
            if col not in df.columns:
                df[col] = ''
        
        df = df[columns]
        
        # Save to XLSX
        output_path = os.path.join(self.output_folder, output_filename)
        df.to_excel(output_path, index=False, engine='openpyxl')
        if len(df) == 0:
            logger.info(f"Saved {len(df)} posts.")
    
    def process_xml_file(self, xml_filepath):
        """Process a single XML file"""
        try:
            logger.info(f"Processing file: {xml_filepath}")
            
            filename = os.path.basename(xml_filepath)
            forum_id = self.extract_forum_id_from_filename(filename)
            
            with open(xml_filepath, 'r', encoding='utf-8') as file:
                xml_content = file.read()
            
            # Parse the XML/HTML content
            posts_data = self.parse_forum_xml(xml_content, forum_id)

            if not posts_data:
                logger.warning(f"No posts found in {xml_filepath}")
                return
            
            # Generate output filename
            base_name = os.path.splitext(os.path.basename(xml_filepath))[0]
            output_filename = f"{base_name}_parsed.xlsx"
            
            # Create XLSX file
            self.create_xlsx_from_posts(posts_data, output_filename)
            
        except Exception as e:
            logger.error(f"Error processing {xml_filepath}: {e}")
    
    def process_all_xml_files(self):
        """Process all XML files in the input folder"""
        if not os.path.exists(self.input_folder):
            logger.error(f"Input folder does not exist: {self.input_folder}")
            return
        
        # Find all XML files
        xml_files = [f for f in os.listdir(self.input_folder) if f.lower().endswith('.xml')]
        
        if not xml_files:
            logger.warning(f"No XML files found in {self.input_folder}")
            return
        
        logger.info(f"Found {len(xml_files)} XML files to process")
        
        # Process each XML file
        for xml_file in xml_files:
            xml_filepath = os.path.join(self.input_folder, xml_file)
            self.process_xml_file(xml_filepath)
        
        logger.info("Processing complete!")

def main():
    """Main function to run the parser"""
    # Initialize parser
    parser = ForumXMLParser()
    
    # Process all XML files
    parser.process_all_xml_files()

if __name__ == "__main__":
    main()