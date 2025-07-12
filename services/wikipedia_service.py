import logging
import requests
from typing import Dict, List, Optional, Any
import re
from datetime import datetime
from bs4 import BeautifulSoup
import time

logger = logging.getLogger(__name__)

class WikipediaService:
    """
    Service for gathering biographical information from Wikipedia
    """
    
    def __init__(self):
        self.base_url = "https://en.wikipedia.org/w/api.php"
        self.rest_url = "https://en.wikipedia.org/api/rest_v1"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PromoterDetailsAgent/1.0 (https://example.com/contact)'
        })
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 1 second between requests
    
    def health_check(self) -> bool:
        """
        Check if Wikipedia API is accessible
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            response = self.session.get(
                self.base_url,
                params={
                    'action': 'query',
                    'format': 'json',
                    'meta': 'siteinfo',
                    'siprop': 'general'
                },
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Wikipedia health check failed: {str(e)}")
            return False
    
    def search_person(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for a person on Wikipedia
        
        Args:
            query: Search query
            
        Returns:
            List of search results
        """
        try:
            self._rate_limit()
            
            # Use OpenSearch API for initial search
            response = self.session.get(
                self.base_url,
                params={
                    'action': 'opensearch',
                    'format': 'json',
                    'search': query,
                    'limit': 10,
                    'namespace': 0  # Main namespace only
                },
                timeout=15
            )
            
            if response.status_code != 200:
                logger.error(f"Wikipedia search failed with status {response.status_code}")
                return []
            
            data = response.json()
            
            if len(data) < 4:
                return []
            
            titles = data[1]
            descriptions = data[2]
            urls = data[3]
            
            results = []
            for i, title in enumerate(titles):
                if i < len(descriptions) and i < len(urls):
                    results.append({
                        'name': title,
                        'description': descriptions[i],
                        'url': urls[i],
                        'relevance_score': 1.0 - (i * 0.1)  # Decrease relevance for lower results
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Wikipedia search failed: {str(e)}")
            return []
    
    def get_person_data(self, person_name: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive biographical data for a person from Wikipedia
        
        Args:
            person_name: Name of the person
            
        Returns:
            Dictionary containing biographical information
        """
        try:
            # First, search for the exact page
            page_data = self._get_page_data(person_name)
            if not page_data:
                return None
            
            # Extract biographical information
            bio_data = self._extract_biographical_info(page_data)
            
            # Get additional structured data
            infobox_data = self._extract_infobox_data(page_data)
            
            # Combine all data
            result = {
                'name': bio_data.get('name', person_name),
                'aliases': bio_data.get('aliases', []),
                'personal_info': {
                    'birth_date': infobox_data.get('birth_date', ''),
                    'age': self._calculate_age(infobox_data.get('birth_date', '')),
                    'birth_year': self._extract_birth_year(infobox_data.get('birth_date', '')),
                    'nationality': infobox_data.get('nationality', ''),
                    'occupation': infobox_data.get('occupation', ''),
                    'death_date': infobox_data.get('death_date', '')
                },
                'family': {
                    'spouse': self._extract_spouse_info(infobox_data),
                    'children': self._extract_children_info(infobox_data),
                    'parents': infobox_data.get('parents', []),
                    'siblings': infobox_data.get('siblings', [])
                },
                'education': self._extract_education_info(infobox_data, page_data),
                'career': self._extract_career_info(infobox_data, page_data),
                'summary': bio_data.get('summary', ''),
                'categories': page_data.get('categories', []),
                'source_url': page_data.get('url', ''),
                'last_updated': datetime.utcnow().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting person data for {person_name}: {str(e)}")
            return None
    
    def _rate_limit(self):
        """Apply rate limiting to respect Wikipedia's servers"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last_request)
        
        self.last_request_time = time.time()
    
    def _get_page_data(self, page_title: str) -> Optional[Dict[str, Any]]:
        """
        Get page data from Wikipedia
        
        Args:
            page_title: Title of the Wikipedia page
            
        Returns:
            Dictionary containing page data
        """
        try:
            self._rate_limit()
            
            # Get page content
            response = self.session.get(
                self.base_url,
                params={
                    'action': 'query',
                    'format': 'json',
                    'titles': page_title,
                    'prop': 'extracts|pageimages|categories|info',
                    'exintro': True,
                    'explaintext': True,
                    'exsectionformat': 'plain',
                    'piprop': 'thumbnail|name',
                    'pithumbsize': 300,
                    'inprop': 'url'
                },
                timeout=15
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            if 'query' not in data or 'pages' not in data['query']:
                return None
            
            pages = data['query']['pages']
            page_id = next(iter(pages.keys()))
            
            if page_id == '-1':  # Page not found
                return None
            
            page = pages[page_id]
            
            # Get full page content for more detailed extraction
            full_content = self._get_full_page_content(page_title)
            
            return {
                'title': page.get('title', ''),
                'extract': page.get('extract', ''),
                'full_content': full_content,
                'thumbnail': page.get('thumbnail', {}).get('source', ''),
                'categories': [cat['title'].replace('Category:', '') for cat in page.get('categories', [])],
                'url': page.get('fullurl', ''),
                'pageid': page_id
            }
            
        except Exception as e:
            logger.error(f"Error getting page data for {page_title}: {str(e)}")
            return None
    
    def _get_full_page_content(self, page_title: str) -> str:
        """
        Get full page content including infobox data
        
        Args:
            page_title: Title of the Wikipedia page
            
        Returns:
            Full page content as text
        """
        try:
            self._rate_limit()
            
            response = self.session.get(
                self.base_url,
                params={
                    'action': 'query',
                    'format': 'json',
                    'titles': page_title,
                    'prop': 'revisions',
                    'rvprop': 'content',
                    'rvslots': 'main'
                },
                timeout=15
            )
            
            if response.status_code != 200:
                return ""
            
            data = response.json()
            
            if 'query' not in data or 'pages' not in data['query']:
                return ""
            
            pages = data['query']['pages']
            page_id = next(iter(pages.keys()))
            
            if page_id == '-1':
                return ""
            
            page = pages[page_id]
            
            if 'revisions' not in page or not page['revisions']:
                return ""
            
            return page['revisions'][0]['slots']['main']['*']
            
        except Exception as e:
            logger.error(f"Error getting full page content for {page_title}: {str(e)}")
            return ""
    
    def _extract_biographical_info(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract basic biographical information from page data
        
        Args:
            page_data: Wikipedia page data
            
        Returns:
            Dictionary containing biographical information
        """
        bio_info = {
            'name': page_data.get('title', ''),
            'aliases': [],
            'summary': page_data.get('extract', '')
        }
        
        # Extract aliases from the full content
        content = page_data.get('full_content', '')
        
        # Look for common alias patterns
        alias_patterns = [
            r'also known as ([^,\n]+)',
            r'née ([^,\n]+)',
            r'born ([^,\n]+)',
            r'formerly ([^,\n]+)'
        ]
        
        for pattern in alias_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                clean_alias = match.strip()
                if clean_alias and clean_alias not in bio_info['aliases']:
                    bio_info['aliases'].append(clean_alias)
        
        return bio_info
    
    def _extract_infobox_data(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured data from Wikipedia infobox
        
        Args:
            page_data: Wikipedia page data
            
        Returns:
            Dictionary containing infobox data
        """
        infobox_data = {}
        content = page_data.get('full_content', '')
        
        # Extract infobox using regex
        infobox_match = re.search(r'\{\{[Ii]nfobox[^}]+\}\}', content, re.DOTALL)
        if not infobox_match:
            return infobox_data
        
        infobox_content = infobox_match.group(0)
        
        # Extract common fields
        field_patterns = {
            'birth_date': r'birth_date\s*=\s*([^\n\|]+)',
            'death_date': r'death_date\s*=\s*([^\n\|]+)',
            'nationality': r'nationality\s*=\s*([^\n\|]+)',
            'occupation': r'occupation\s*=\s*([^\n\|]+)',
            'education': r'education\s*=\s*([^\n\|]+)',
            'alma_mater': r'alma_mater\s*=\s*([^\n\|]+)',
            'spouse': r'spouse\s*=\s*([^\n\|]+)',
            'children': r'children\s*=\s*([^\n\|]+)',
            'parents': r'parents\s*=\s*([^\n\|]+)',
            'employer': r'employer\s*=\s*([^\n\|]+)',
            'known_for': r'known_for\s*=\s*([^\n\|]+)'
        }
        
        for field, pattern in field_patterns.items():
            matches = re.findall(pattern, infobox_content, re.IGNORECASE)
            if matches:
                # Clean up the match
                value = matches[0].strip()
                value = re.sub(r'\{\{[^}]+\}\}', '', value)  # Remove templates
                value = re.sub(r'\[\[([^\]]+)\]\]', r'\1', value)  # Remove wiki links
                value = value.strip()
                if value:
                    infobox_data[field] = value
        
        return infobox_data
    
    def _extract_spouse_info(self, infobox_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract spouse information from infobox data"""
        spouse_info = {}
        
        spouse_text = infobox_data.get('spouse', '')
        if spouse_text:
            # Try to extract name and marriage year
            name_match = re.search(r'([^(]+)', spouse_text)
            if name_match:
                spouse_info['name'] = name_match.group(1).strip()
            
            # Look for marriage year
            year_match = re.search(r'\((?:m\.|married)\s*(\d{4})', spouse_text)
            if year_match:
                spouse_info['marriage_year'] = year_match.group(1)
        
        return spouse_info
    
    def _extract_children_info(self, infobox_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract children information from infobox data"""
        children = []
        
        children_text = infobox_data.get('children', '')
        if children_text:
            # Try to extract number of children
            number_match = re.search(r'(\d+)', children_text)
            if number_match:
                num_children = int(number_match.group(1))
                for i in range(num_children):
                    children.append({'name': f'Child {i+1}', 'age': 'Unknown'})
        
        return children
    
    def _extract_education_info(self, infobox_data: Dict[str, Any], 
                              page_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract education information"""
        education = []
        
        # From infobox
        education_text = infobox_data.get('education', '') or infobox_data.get('alma_mater', '')
        if education_text:
            education.append({
                'institution': education_text,
                'degree': 'Unknown',
                'year': 'Unknown'
            })
        
        # Try to extract from main content
        content = page_data.get('extract', '')
        
        # Look for education mentions
        education_patterns = [
            r'graduated from ([^,\n]+)',
            r'attended ([^,\n]+)',
            r'studied at ([^,\n]+)',
            r'earned.*degree from ([^,\n]+)'
        ]
        
        for pattern in education_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                institution = match.strip()
                if institution and not any(edu['institution'] == institution for edu in education):
                    education.append({
                        'institution': institution,
                        'degree': 'Unknown',
                        'year': 'Unknown'
                    })
        
        return education
    
    def _extract_career_info(self, infobox_data: Dict[str, Any], 
                           page_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract career information"""
        career = []
        
        # From infobox
        occupation = infobox_data.get('occupation', '')
        employer = infobox_data.get('employer', '')
        known_for = infobox_data.get('known_for', '')
        
        if occupation or employer:
            career.append({
                'title': occupation,
                'company': employer,
                'duration': 'Unknown',
                'description': known_for
            })
        
        return career
    
    def _calculate_age(self, birth_date: str) -> str:
        """Calculate age from birth date"""
        if not birth_date:
            return ""
        
        # Extract year from birth date
        year_match = re.search(r'(\d{4})', birth_date)
        if year_match:
            birth_year = int(year_match.group(1))
            current_year = datetime.now().year
            age = current_year - birth_year
            return str(age)
        
        return ""
    
    def _extract_birth_year(self, birth_date: str) -> str:
        """Extract birth year from birth date"""
        if not birth_date:
            return ""
        
        year_match = re.search(r'(\d{4})', birth_date)
        if year_match:
            return year_match.group(1)
        
        return ""