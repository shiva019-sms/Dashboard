import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ConfidenceCalculator:
    """
    Utility class for calculating confidence scores for aggregated data
    """
    
    def __init__(self):
        # Source reliability weights
        self.source_weights = {
            'wikipedia': 0.8,      # High reliability for biographical data
            'news': 0.6,           # Medium reliability, recent but less comprehensive
            'crunchbase': 0.7,     # Good for business information
            'linkedin': 0.7,       # Good for professional information
            'official_records': 0.9,  # Highest reliability
            'social_media': 0.4,   # Lower reliability
            'web_scraping': 0.3    # Lowest reliability
        }
        
        # Field importance weights for promoter profile
        self.field_weights = {
            'name': 0.15,                    # Very important
            'personal_info': 0.15,           # Very important (age, DOB)
            'family_info': 0.12,             # Important (spouse, children)
            'education': 0.12,               # Important
            'work_history': 0.18,            # Very important (professional background)
            'connections': 0.10,             # Moderately important
            'financial_info': 0.08,          # Important but often private
            'interests': 0.05,               # Less important
            'investments': 0.05              # Less important but relevant
        }
        
        # Data freshness decay factors
        self.freshness_decay = {
            'news': 30,           # News data loses relevance after 30 days
            'wikipedia': 365,     # Wikipedia data stays relevant longer
            'social_media': 7,    # Social media data decays quickly
            'official_records': 1825  # Official records stay relevant for ~5 years
        }
    
    def calculate_overall_confidence(self, source_data: Dict[str, Any], 
                                   aggregated_data: Dict[str, Any]) -> float:
        """
        Calculate overall confidence score for the aggregated profile
        
        Args:
            source_data: Raw data from all sources
            aggregated_data: Processed and aggregated data
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        try:
            # Calculate source quality score
            source_score = self._calculate_source_quality_score(source_data)
            
            # Calculate data completeness score
            completeness_score = self._calculate_completeness_score(aggregated_data)
            
            # Calculate data consistency score
            consistency_score = self._calculate_consistency_score(source_data)
            
            # Calculate freshness score
            freshness_score = self._calculate_freshness_score(source_data)
            
            # Weighted combination
            overall_score = (
                source_score * 0.3 +
                completeness_score * 0.35 +
                consistency_score * 0.25 +
                freshness_score * 0.1
            )
            
            # Apply penalties for missing critical information
            penalty = self._calculate_missing_critical_info_penalty(aggregated_data)
            overall_score = max(0.0, overall_score - penalty)
            
            return round(min(overall_score, 1.0), 3)
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {str(e)}")
            return 0.0
    
    def _calculate_source_quality_score(self, source_data: Dict[str, Any]) -> float:
        """Calculate score based on source quality and reliability"""
        if not source_data:
            return 0.0
        
        total_weight = 0.0
        weighted_score = 0.0
        
        for source_name, data in source_data.items():
            if not data:
                continue
            
            source_weight = self.source_weights.get(source_name, 0.3)
            data_quality = self._assess_source_data_quality(data, source_name)
            
            weighted_score += source_weight * data_quality
            total_weight += source_weight
        
        return weighted_score / total_weight if total_weight > 0 else 0.0
    
    def _calculate_completeness_score(self, aggregated_data: Dict[str, Any]) -> float:
        """Calculate score based on data completeness"""
        if not aggregated_data:
            return 0.0
        
        total_weight = 0.0
        weighted_score = 0.0
        
        for field, weight in self.field_weights.items():
            total_weight += weight
            
            if field in aggregated_data:
                field_score = self._calculate_field_completeness(
                    aggregated_data[field], field
                )
                weighted_score += weight * field_score
        
        return weighted_score / total_weight if total_weight > 0 else 0.0
    
    def _calculate_consistency_score(self, source_data: Dict[str, Any]) -> float:
        """Calculate score based on data consistency across sources"""
        if len(source_data) <= 1:
            return 1.0  # Perfect consistency with single source
        
        consistency_checks = []
        
        # Check name consistency
        names = []
        for source, data in source_data.items():
            if isinstance(data, dict) and 'name' in data:
                names.append(data['name'])
        
        name_consistency = self._calculate_field_consistency(names)
        consistency_checks.append(name_consistency)
        
        # Check birth year consistency
        birth_years = []
        for source, data in source_data.items():
            if isinstance(data, dict):
                # Try different paths for birth year
                birth_year = (
                    data.get('personal_info', {}).get('birth_year') or
                    data.get('birth_year') or
                    self._extract_year_from_date(data.get('personal_info', {}).get('birth_date', ''))
                )
                if birth_year:
                    birth_years.append(str(birth_year))
        
        birth_year_consistency = self._calculate_field_consistency(birth_years)
        consistency_checks.append(birth_year_consistency)
        
        # Check occupation consistency
        occupations = []
        for source, data in source_data.items():
            if isinstance(data, dict):
                occupation = (
                    data.get('personal_info', {}).get('occupation') or
                    data.get('occupation')
                )
                if occupation:
                    occupations.append(occupation.lower())
        
        occupation_consistency = self._calculate_field_consistency(occupations)
        consistency_checks.append(occupation_consistency)
        
        # Average consistency scores
        return sum(consistency_checks) / len(consistency_checks) if consistency_checks else 1.0
    
    def _calculate_freshness_score(self, source_data: Dict[str, Any]) -> float:
        """Calculate score based on data freshness"""
        freshness_scores = []
        
        for source_name, data in source_data.items():
            if not isinstance(data, dict):
                continue
            
            # Get last updated date
            last_updated = data.get('last_updated') or data.get('timestamp')
            if not last_updated:
                # Assign default age based on source type
                if source_name == 'wikipedia':
                    days_old = 30  # Assume moderately fresh
                elif source_name == 'news':
                    days_old = 7   # Assume recent
                else:
                    days_old = 90  # Assume older
            else:
                days_old = self._calculate_days_since_update(last_updated)
            
            # Calculate freshness score based on source type
            decay_period = self.freshness_decay.get(source_name, 365)
            freshness = max(0.0, 1.0 - (days_old / decay_period))
            freshness_scores.append(freshness)
        
        return sum(freshness_scores) / len(freshness_scores) if freshness_scores else 0.5
    
    def _assess_source_data_quality(self, data: Dict[str, Any], source_name: str) -> float:
        """Assess the quality of data from a specific source"""
        if not data:
            return 0.0
        
        quality_indicators = []
        
        # Check for structured data
        if isinstance(data, dict):
            quality_indicators.append(0.3)
            
            # Check for key biographical fields
            key_fields = ['name', 'age', 'occupation', 'education', 'family']
            found_fields = sum(1 for field in key_fields if field in data)
            field_score = found_fields / len(key_fields)
            quality_indicators.append(field_score * 0.4)
            
            # Check for detailed information
            detail_score = 0.0
            if 'education' in data and isinstance(data['education'], list) and data['education']:
                detail_score += 0.1
            if 'career' in data and isinstance(data['career'], list) and data['career']:
                detail_score += 0.1
            if 'family' in data and isinstance(data['family'], dict) and data['family']:
                detail_score += 0.1
            
            quality_indicators.append(detail_score)
        else:
            quality_indicators.append(0.1)  # Unstructured data gets low score
        
        return min(sum(quality_indicators), 1.0)
    
    def _calculate_field_completeness(self, field_data: Any, field_name: str) -> float:
        """Calculate completeness score for a specific field"""
        if not field_data:
            return 0.0
        
        if isinstance(field_data, str):
            return 1.0 if field_data.strip() else 0.0
        
        elif isinstance(field_data, list):
            if not field_data:
                return 0.0
            # Score based on number of items, with diminishing returns
            return min(len(field_data) / 3.0, 1.0)
        
        elif isinstance(field_data, dict):
            if not field_data:
                return 0.0
            
            # Field-specific scoring
            if field_name == 'personal_info':
                required_fields = ['birth_date', 'age', 'nationality']
                found = sum(1 for field in required_fields if field_data.get(field))
                return found / len(required_fields)
            
            elif field_name == 'family_info':
                possible_fields = ['spouse', 'children', 'parents']
                found = sum(1 for field in possible_fields if field_data.get(field))
                return found / len(possible_fields)
            
            else:
                # Generic dict scoring
                filled_fields = sum(1 for v in field_data.values() if v)
                total_fields = len(field_data)
                return filled_fields / total_fields if total_fields > 0 else 0.0
        
        return 0.5  # Default for unknown types
    
    def _calculate_field_consistency(self, values: List[str]) -> float:
        """Calculate consistency score for a field across sources"""
        if not values:
            return 1.0
        
        if len(values) == 1:
            return 1.0
        
        # Normalize values for comparison
        normalized_values = [v.lower().strip() for v in values if v]
        
        if not normalized_values:
            return 1.0
        
        # Check if all values are the same
        unique_values = set(normalized_values)
        
        if len(unique_values) == 1:
            return 1.0
        
        # Calculate similarity for names (allowing for variations)
        if len(unique_values) <= 3:
            # Check for partial matches or variations
            similarity_score = 0.0
            total_comparisons = 0
            
            for i, val1 in enumerate(normalized_values):
                for j, val2 in enumerate(normalized_values[i+1:], i+1):
                    similarity = self._calculate_string_similarity(val1, val2)
                    similarity_score += similarity
                    total_comparisons += 1
            
            return similarity_score / total_comparisons if total_comparisons > 0 else 0.0
        
        # Too many different values
        return 0.3
    
    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings"""
        if str1 == str2:
            return 1.0
        
        # Simple similarity based on common words
        words1 = set(str1.split())
        words2 = set(str2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _extract_year_from_date(self, date_str: str) -> Optional[str]:
        """Extract year from date string"""
        if not date_str:
            return None
        
        import re
        year_match = re.search(r'(\d{4})', str(date_str))
        return year_match.group(1) if year_match else None
    
    def _calculate_days_since_update(self, timestamp_str: str) -> int:
        """Calculate days since last update"""
        try:
            if isinstance(timestamp_str, str):
                # Try to parse ISO format
                if 'T' in timestamp_str:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                else:
                    timestamp = datetime.fromisoformat(timestamp_str)
            else:
                return 30  # Default
            
            now = datetime.now(timestamp.tzinfo) if timestamp.tzinfo else datetime.now()
            delta = now - timestamp
            return delta.days
            
        except Exception:
            return 30  # Default to 30 days if parsing fails
    
    def _calculate_missing_critical_info_penalty(self, aggregated_data: Dict[str, Any]) -> float:
        """Calculate penalty for missing critical information"""
        penalty = 0.0
        
        # Critical fields for promoter profile
        critical_fields = {
            'name': 0.15,
            'personal_info': 0.10,
            'work_history': 0.10
        }
        
        for field, penalty_weight in critical_fields.items():
            if field not in aggregated_data or not aggregated_data[field]:
                penalty += penalty_weight
        
        # Additional penalty for completely empty profile
        if not any(aggregated_data.get(field) for field in self.field_weights.keys()):
            penalty += 0.3
        
        return penalty
    
    def get_confidence_breakdown(self, source_data: Dict[str, Any], 
                               aggregated_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Get detailed breakdown of confidence scoring
        
        Args:
            source_data: Raw data from all sources
            aggregated_data: Processed and aggregated data
            
        Returns:
            Dictionary with confidence score breakdown
        """
        try:
            breakdown = {
                'source_quality': self._calculate_source_quality_score(source_data),
                'data_completeness': self._calculate_completeness_score(aggregated_data),
                'data_consistency': self._calculate_consistency_score(source_data),
                'data_freshness': self._calculate_freshness_score(source_data),
                'missing_critical_penalty': self._calculate_missing_critical_info_penalty(aggregated_data)
            }
            
            # Calculate overall score
            breakdown['overall_score'] = self.calculate_overall_confidence(source_data, aggregated_data)
            
            return breakdown
            
        except Exception as e:
            logger.error(f"Error generating confidence breakdown: {str(e)}")
            return {'overall_score': 0.0}