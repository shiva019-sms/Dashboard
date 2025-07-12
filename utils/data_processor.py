import re
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import unicodedata

logger = logging.getLogger(__name__)

class DataProcessor:
    """
    Utility class for processing and normalizing data from various sources
    """
    
    def __init__(self):
        # Common company suffixes
        self.company_suffixes = [
            'inc', 'inc.', 'corp', 'corp.', 'corporation', 'company', 'co', 'co.',
            'ltd', 'ltd.', 'limited', 'llc', 'l.l.c.', 'lp', 'l.p.',
            'technologies', 'tech', 'systems', 'solutions', 'services',
            'group', 'holdings', 'international', 'intl'
        ]
        
        # Common title prefixes and suffixes
        self.name_prefixes = ['dr', 'mr', 'mrs', 'ms', 'prof', 'professor']
        self.name_suffixes = ['jr', 'sr', 'ii', 'iii', 'iv', 'v', 'phd', 'md']
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize text for consistent processing
        
        Args:
            text: Input text
            
        Returns:
            Normalized text
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Convert to lowercase for processing
        text = text.lower()
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\-.,;:!?()\'"@#$%&*+=]', '', text)
        
        # Normalize unicode characters
        text = unicodedata.normalize('NFKD', text)
        
        return text.strip()
    
    def normalize_name(self, name: str) -> str:
        """
        Normalize person name
        
        Args:
            name: Person name
            
        Returns:
            Normalized name
        """
        if not name or not isinstance(name, str):
            return ""
        
        # Basic cleaning
        name = ' '.join(name.split())
        
        # Remove common prefixes and suffixes for normalization
        parts = name.lower().split()
        cleaned_parts = []
        
        for part in parts:
            # Remove dots and convert to lowercase for comparison
            clean_part = part.replace('.', '').lower()
            
            # Skip prefixes and suffixes
            if clean_part not in self.name_prefixes and clean_part not in self.name_suffixes:
                # Keep original case
                cleaned_parts.append(part)
        
        # Convert to title case
        normalized = ' '.join(cleaned_parts).title()
        
        return normalized
    
    def normalize_company_name(self, company: str) -> str:
        """
        Normalize company name
        
        Args:
            company: Company name
            
        Returns:
            Normalized company name
        """
        if not company or not isinstance(company, str):
            return ""
        
        # Basic cleaning
        company = ' '.join(company.split())
        
        # Convert to title case
        company = company.title()
        
        # Handle common abbreviations
        company = company.replace(' Inc.', ' Inc.')
        company = company.replace(' Corp.', ' Corp.')
        company = company.replace(' Ltd.', ' Ltd.')
        company = company.replace(' Llc', ' LLC')
        
        return company
    
    def extract_dates(self, text: str) -> List[str]:
        """
        Extract date patterns from text
        
        Args:
            text: Input text
            
        Returns:
            List of found dates
        """
        if not text:
            return []
        
        date_patterns = [
            r'\b\d{1,2}/\d{1,2}/\d{4}\b',  # MM/DD/YYYY
            r'\b\d{1,2}-\d{1,2}-\d{4}\b',  # MM-DD-YYYY
            r'\b\d{4}-\d{1,2}-\d{1,2}\b',  # YYYY-MM-DD
            r'\b\d{4}\b',                   # YYYY
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
            r'\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b'
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)
        
        return list(set(dates))  # Remove duplicates
    
    def extract_years(self, text: str) -> List[str]:
        """
        Extract year patterns from text
        
        Args:
            text: Input text
            
        Returns:
            List of found years
        """
        if not text:
            return []
        
        # Look for 4-digit years between 1900 and current year + 10
        current_year = datetime.now().year
        year_pattern = r'\b(19\d{2}|20[0-4]\d)\b'
        
        years = re.findall(year_pattern, text)
        
        # Filter to reasonable range
        valid_years = []
        for year in years:
            year_int = int(year)
            if 1900 <= year_int <= current_year + 10:
                valid_years.append(year)
        
        return list(set(valid_years))
    
    def clean_html(self, text: str) -> str:
        """
        Remove HTML tags from text
        
        Args:
            text: Text with HTML tags
            
        Returns:
            Clean text
        """
        if not text:
            return ""
        
        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', '', text)
        
        # Decode HTML entities
        clean_text = clean_text.replace('&amp;', '&')
        clean_text = clean_text.replace('&lt;', '<')
        clean_text = clean_text.replace('&gt;', '>')
        clean_text = clean_text.replace('&quot;', '"')
        clean_text = clean_text.replace('&#39;', "'")
        clean_text = clean_text.replace('&nbsp;', ' ')
        
        # Remove extra whitespace
        clean_text = ' '.join(clean_text.split())
        
        return clean_text
    
    def merge_duplicate_entries(self, entries: List[Dict[str, Any]], 
                              key_field: str) -> List[Dict[str, Any]]:
        """
        Merge duplicate entries based on a key field
        
        Args:
            entries: List of entries to merge
            key_field: Field to use for deduplication
            
        Returns:
            List of merged entries
        """
        if not entries:
            return []
        
        merged = {}
        
        for entry in entries:
            if not isinstance(entry, dict) or key_field not in entry:
                continue
            
            key = entry[key_field].lower().strip()
            
            if key in merged:
                # Merge entries
                merged[key] = self._merge_entries(merged[key], entry)
            else:
                merged[key] = entry.copy()
        
        return list(merged.values())
    
    def _merge_entries(self, entry1: Dict[str, Any], 
                      entry2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge two entries, preferring non-empty values
        
        Args:
            entry1: First entry
            entry2: Second entry
            
        Returns:
            Merged entry
        """
        merged = entry1.copy()
        
        for key, value in entry2.items():
            if key not in merged or not merged[key]:
                merged[key] = value
            elif isinstance(value, list) and isinstance(merged[key], list):
                # Merge lists and remove duplicates
                merged[key] = list(set(merged[key] + value))
            elif isinstance(value, str) and value and len(value) > len(str(merged[key])):
                # Prefer longer string values
                merged[key] = value
        
        return merged
    
    def standardize_phone_number(self, phone: str) -> str:
        """
        Standardize phone number format
        
        Args:
            phone: Phone number string
            
        Returns:
            Standardized phone number
        """
        if not phone:
            return ""
        
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        
        # Handle different formats
        if len(digits) == 10:
            # US format
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            # US format with country code
            return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        else:
            # Return original if not standard format
            return phone
    
    def extract_email_addresses(self, text: str) -> List[str]:
        """
        Extract email addresses from text
        
        Args:
            text: Input text
            
        Returns:
            List of email addresses
        """
        if not text:
            return []
        
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        
        # Validate and clean emails
        valid_emails = []
        for email in emails:
            email = email.lower().strip()
            if self._is_valid_email(email):
                valid_emails.append(email)
        
        return list(set(valid_emails))
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def calculate_confidence_score(self, data: Dict[str, Any], 
                                 source_weights: Dict[str, float]) -> float:
        """
        Calculate confidence score for aggregated data
        
        Args:
            data: Aggregated data
            source_weights: Weights for different sources
            
        Returns:
            Confidence score between 0 and 1
        """
        if not data:
            return 0.0
        
        # Count filled fields
        filled_fields = 0
        total_fields = 0
        weighted_score = 0.0
        
        # Define important fields and their weights
        field_weights = {
            'name': 0.2,
            'personal_info': 0.15,
            'education': 0.15,
            'work_history': 0.2,
            'family_info': 0.1,
            'connections': 0.1,
            'interests': 0.05,
            'investments': 0.05
        }
        
        for field, weight in field_weights.items():
            total_fields += 1
            
            if field in data and data[field]:
                filled_fields += 1
                
                # Calculate field-specific score
                field_score = self._calculate_field_score(data[field])
                weighted_score += weight * field_score
        
        # Apply source reliability
        source_bonus = 0.0
        if 'sources' in data:
            for source in data['sources']:
                source_bonus += source_weights.get(source, 0.0)
        
        # Normalize source bonus
        if source_bonus > 0:
            source_bonus = min(source_bonus / len(source_weights), 0.2)
        
        # Calculate final score
        final_score = min(weighted_score + source_bonus, 1.0)
        
        return round(final_score, 2)
    
    def _calculate_field_score(self, field_data: Any) -> float:
        """Calculate score for individual field"""
        if not field_data:
            return 0.0
        
        if isinstance(field_data, str):
            return 1.0 if field_data.strip() else 0.0
        elif isinstance(field_data, list):
            return min(len(field_data) / 3.0, 1.0)  # Max score at 3+ items
        elif isinstance(field_data, dict):
            filled_keys = sum(1 for v in field_data.values() if v)
            total_keys = len(field_data)
            return filled_keys / total_keys if total_keys > 0 else 0.0
        
        return 0.5  # Default for other types