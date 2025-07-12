from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime

@dataclass
class PromoterProfile:
    """
    Structured representation of a promoter profile matching the format
    shown in the user's image.
    """
    
    def __init__(self, data: Dict[str, Any]):
        self.raw_data = data
        self._process_data()
    
    def _process_data(self):
        """Process raw data into structured format"""
        self.name = self._extract_name()
        self.dob_age = self._extract_dob_age()
        self.spouse_name_and_age = self._extract_spouse_info()
        self.children_names_and_ages = self._extract_children_info()
        self.educational_background = self._extract_education()
        self.professional_background = self._extract_professional_background()
        self.private_banker = self._extract_private_banker()
        self.icici_bank_relationship = self._extract_icici_relationship()
        self.key_connections = self._extract_key_connections()
        self.area_of_interest_investments = self._extract_interests_investments()
        
        # Metadata
        self.confidence_score = self.raw_data.get('confidence_score', 0.0)
        self.sources_used = self.raw_data.get('sources', [])
        self.last_updated = datetime.utcnow().isoformat()
    
    def _extract_name(self) -> str:
        """Extract full name and aliases"""
        name_data = self.raw_data.get('name', {})
        if isinstance(name_data, str):
            return name_data
        
        full_name = name_data.get('full_name', '')
        aliases = name_data.get('aliases', [])
        
        if aliases:
            return f"{full_name} (also known as: {', '.join(aliases)})"
        return full_name
    
    def _extract_dob_age(self) -> str:
        """Extract date of birth and age information"""
        personal_info = self.raw_data.get('personal_info', {})
        
        dob = personal_info.get('date_of_birth', '')
        age = personal_info.get('age', '')
        birth_year = personal_info.get('birth_year', '')
        
        if dob:
            return f"DOB: {dob}"
        elif age:
            return f"Age: {age}"
        elif birth_year:
            return f"Birth Year: {birth_year}"
        
        return "Not available"
    
    def _extract_spouse_info(self) -> str:
        """Extract spouse information"""
        family_info = self.raw_data.get('family_info', {})
        spouse = family_info.get('spouse', {})
        
        if not spouse:
            return "Not available"
        
        spouse_name = spouse.get('name', '')
        spouse_age = spouse.get('age', '')
        
        if spouse_name and spouse_age:
            return f"{spouse_name} (Age: {spouse_age})"
        elif spouse_name:
            return spouse_name
        
        return "Not available"
    
    def _extract_children_info(self) -> List[str]:
        """Extract children information"""
        family_info = self.raw_data.get('family_info', {})
        children = family_info.get('children', [])
        
        if not children:
            return ["Not available"]
        
        children_info = []
        for child in children:
            if isinstance(child, dict):
                name = child.get('name', '')
                age = child.get('age', '')
                if name and age:
                    children_info.append(f"{name} (Age: {age})")
                elif name:
                    children_info.append(name)
            elif isinstance(child, str):
                children_info.append(child)
        
        return children_info if children_info else ["Not available"]
    
    def _extract_education(self) -> List[str]:
        """Extract educational background"""
        education = self.raw_data.get('education', [])
        
        if not education:
            return ["Not available"]
        
        education_info = []
        for edu in education:
            if isinstance(edu, dict):
                institution = edu.get('institution', '')
                degree = edu.get('degree', '')
                year = edu.get('year', '')
                
                if institution and degree:
                    edu_str = f"{degree} from {institution}"
                    if year:
                        edu_str += f" ({year})"
                    education_info.append(edu_str)
                elif institution:
                    education_info.append(institution)
            elif isinstance(edu, str):
                education_info.append(edu)
        
        return education_info if education_info else ["Not available"]
    
    def _extract_professional_background(self) -> List[str]:
        """Extract professional background"""
        work_history = self.raw_data.get('work_history', [])
        
        if not work_history:
            return ["Not available"]
        
        professional_info = []
        for job in work_history:
            if isinstance(job, dict):
                title = job.get('title', '')
                company = job.get('company', '')
                duration = job.get('duration', '')
                
                if title and company:
                    job_str = f"{title} at {company}"
                    if duration:
                        job_str += f" ({duration})"
                    professional_info.append(job_str)
                elif company:
                    professional_info.append(company)
            elif isinstance(job, str):
                professional_info.append(job)
        
        return professional_info if professional_info else ["Not available"]
    
    def _extract_private_banker(self) -> str:
        """Extract private banking relationships"""
        financial_info = self.raw_data.get('financial_info', {})
        private_banker = financial_info.get('private_banker', '')
        
        if private_banker:
            return private_banker
        
        # Check for banking relationships in connections
        connections = self.raw_data.get('connections', [])
        for connection in connections:
            if isinstance(connection, dict):
                if 'bank' in connection.get('type', '').lower():
                    return connection.get('name', '')
        
        return "Not available"
    
    def _extract_icici_relationship(self) -> str:
        """Extract ICICI Bank specific relationships"""
        financial_info = self.raw_data.get('financial_info', {})
        icici_info = financial_info.get('icici_bank', '')
        
        if icici_info:
            return icici_info
        
        # Check for ICICI mentions in connections or other data
        connections = self.raw_data.get('connections', [])
        for connection in connections:
            if isinstance(connection, dict):
                name = connection.get('name', '').lower()
                if 'icici' in name:
                    return connection.get('name', '')
        
        return "Not available"
    
    def _extract_key_connections(self) -> Dict[str, List[str]]:
        """Extract key connections categorized by type"""
        connections = self.raw_data.get('connections', [])
        
        categorized_connections = {
            'family': [],
            'friends': [],
            'professional': [],
            'social_network': []
        }
        
        if not connections:
            return {
                'family': ["Not available"],
                'friends': ["Not available"],
                'professional': ["Not available"],
                'social_network': ["Not available"]
            }
        
        for connection in connections:
            if isinstance(connection, dict):
                name = connection.get('name', '')
                conn_type = connection.get('type', '').lower()
                
                if 'family' in conn_type or 'relative' in conn_type:
                    categorized_connections['family'].append(name)
                elif 'friend' in conn_type:
                    categorized_connections['friends'].append(name)
                elif 'professional' in conn_type or 'business' in conn_type:
                    categorized_connections['professional'].append(name)
                else:
                    categorized_connections['social_network'].append(name)
            elif isinstance(connection, str):
                categorized_connections['social_network'].append(connection)
        
        # Ensure each category has at least "Not available" if empty
        for category in categorized_connections:
            if not categorized_connections[category]:
                categorized_connections[category] = ["Not available"]
        
        return categorized_connections
    
    def _extract_interests_investments(self) -> List[str]:
        """Extract areas of interest and investments"""
        interests = self.raw_data.get('interests', [])
        investments = self.raw_data.get('investments', [])
        
        combined_info = []
        
        if interests:
            combined_info.extend([f"Interest: {item}" for item in interests])
        
        if investments:
            for investment in investments:
                if isinstance(investment, dict):
                    company = investment.get('company', '')
                    amount = investment.get('amount', '')
                    if company and amount:
                        combined_info.append(f"Investment: {company} ({amount})")
                    elif company:
                        combined_info.append(f"Investment: {company}")
                elif isinstance(investment, str):
                    combined_info.append(f"Investment: {investment}")
        
        return combined_info if combined_info else ["Not available"]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format matching promoter details structure"""
        return {
            "promoter_details": {
                "name": self.name,
                "dob_age": self.dob_age,
                "spouse_name_and_age": self.spouse_name_and_age,
                "children_names_and_ages": self.children_names_and_ages,
                "educational_background": self.educational_background,
                "professional_background": self.professional_background,
                "private_banker": self.private_banker,
                "icici_bank_relationship": self.icici_bank_relationship,
                "key_connections": self.key_connections,
                "area_of_interest_investments": self.area_of_interest_investments
            },
            "metadata": {
                "confidence_score": self.confidence_score,
                "sources_used": self.sources_used,
                "last_updated": self.last_updated
            }
        }
    
    def to_formatted_string(self) -> str:
        """Convert to formatted string representation"""
        output = []
        output.append("=== PROMOTER DETAILS ===")
        output.append(f"Name: {self.name}")
        output.append(f"DOB/Age: {self.dob_age}")
        output.append(f"Spouse Name and Age: {self.spouse_name_and_age}")
        output.append(f"Children Names and Ages: {', '.join(self.children_names_and_ages)}")
        output.append(f"Educational Background: {', '.join(self.educational_background)}")
        output.append(f"Professional Background: {', '.join(self.professional_background)}")
        output.append(f"Private Banker: {self.private_banker}")
        output.append(f"ICICI Bank Relationship: {self.icici_bank_relationship}")
        
        output.append("\nKey Connections:")
        for category, connections in self.key_connections.items():
            output.append(f"  {category.replace('_', ' ').title()}: {', '.join(connections)}")
        
        output.append(f"\nArea of Interest/Investments: {', '.join(self.area_of_interest_investments)}")
        
        output.append(f"\nConfidence Score: {self.confidence_score}")
        output.append(f"Sources Used: {', '.join(self.sources_used)}")
        output.append(f"Last Updated: {self.last_updated}")
        
        return "\n".join(output)