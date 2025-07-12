import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

from services.wikipedia_service import WikipediaService
from services.news_service import NewsService
from utils.data_processor import DataProcessor
from utils.confidence_calculator import ConfidenceCalculator

logger = logging.getLogger(__name__)

class DataAggregator:
    """
    Aggregates data from multiple sources to create comprehensive profiles
    """
    
    def __init__(self):
        self.wikipedia_service = WikipediaService()
        self.news_service = NewsService()
        self.data_processor = DataProcessor()
        self.confidence_calculator = ConfidenceCalculator()
        
        # Data source configurations
        self.sources = {
            'wikipedia': {
                'service': self.wikipedia_service,
                'weight': 0.4,  # Wikipedia is reliable for biographical data
                'enabled': True
            },
            'news': {
                'service': self.news_service,
                'weight': 0.3,  # News provides recent information
                'enabled': True
            },
            # Future sources can be added here
            'crunchbase': {
                'service': None,  # To be implemented
                'weight': 0.2,
                'enabled': False
            },
            'social_media': {
                'service': None,  # To be implemented
                'weight': 0.1,
                'enabled': False
            }
        }
    
    def gather_comprehensive_data(self, name: str, title: str = '', 
                                 company: str = '', context: str = '') -> Dict[str, Any]:
        """
        Gather comprehensive data from all available sources
        
        Args:
            name: Person's name
            title: Professional title (optional)
            company: Company name (optional)
            context: Additional context (optional)
            
        Returns:
            Dictionary containing aggregated data
        """
        logger.info(f"Starting comprehensive data gathering for: {name}")
        
        # Prepare search parameters
        search_params = {
            'name': name,
            'title': title,
            'company': company,
            'context': context
        }
        
        # Collect data from all sources
        source_data = self._collect_from_all_sources(search_params)
        
        # Aggregate and process data
        aggregated_data = self._aggregate_data(source_data)
        
        # Calculate confidence score
        confidence_score = self.confidence_calculator.calculate_overall_confidence(
            source_data, aggregated_data
        )
        
        # Add metadata
        aggregated_data['confidence_score'] = confidence_score
        aggregated_data['sources'] = list(source_data.keys())
        aggregated_data['search_params'] = search_params
        aggregated_data['timestamp'] = datetime.utcnow().isoformat()
        
        logger.info(f"Data gathering completed for: {name}, confidence: {confidence_score}")
        
        return aggregated_data
    
    def search_person(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for a person across multiple sources
        
        Args:
            query: Search query
            
        Returns:
            List of search results
        """
        logger.info(f"Searching for person: {query}")
        
        search_results = []
        
        # Search Wikipedia
        try:
            wiki_results = self.wikipedia_service.search_person(query)
            for result in wiki_results:
                result['source'] = 'wikipedia'
                search_results.append(result)
        except Exception as e:
            logger.error(f"Wikipedia search failed: {str(e)}")
        
        # Search News
        try:
            news_results = self.news_service.search_person(query)
            for result in news_results:
                result['source'] = 'news'
                search_results.append(result)
        except Exception as e:
            logger.error(f"News search failed: {str(e)}")
        
        # Remove duplicates and rank results
        search_results = self._deduplicate_and_rank_search_results(search_results)
        
        return search_results
    
    def get_sources_status(self) -> Dict[str, Any]:
        """
        Get status of all data sources
        
        Returns:
            Dictionary containing source status information
        """
        status = {}
        
        for source_name, source_config in self.sources.items():
            if source_config['enabled'] and source_config['service']:
                try:
                    # Test the service
                    service_status = source_config['service'].health_check()
                    status[source_name] = {
                        'enabled': True,
                        'status': 'healthy' if service_status else 'unhealthy',
                        'weight': source_config['weight']
                    }
                except Exception as e:
                    status[source_name] = {
                        'enabled': True,
                        'status': 'error',
                        'error': str(e),
                        'weight': source_config['weight']
                    }
            else:
                status[source_name] = {
                    'enabled': False,
                    'status': 'disabled',
                    'weight': source_config['weight']
                }
        
        return status
    
    def _collect_from_all_sources(self, search_params: Dict[str, str]) -> Dict[str, Any]:
        """
        Collect data from all enabled sources concurrently
        
        Args:
            search_params: Search parameters
            
        Returns:
            Dictionary containing data from all sources
        """
        source_data = {}
        
        # Use ThreadPoolExecutor for concurrent data collection
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_source = {}
            
            for source_name, source_config in self.sources.items():
                if source_config['enabled'] and source_config['service']:
                    future = executor.submit(
                        self._collect_from_source,
                        source_name,
                        source_config['service'],
                        search_params
                    )
                    future_to_source[future] = source_name
            
            # Collect results
            for future in as_completed(future_to_source):
                source_name = future_to_source[future]
                try:
                    data = future.result(timeout=30)  # 30 second timeout
                    if data:
                        source_data[source_name] = data
                        logger.info(f"Successfully collected data from {source_name}")
                    else:
                        logger.warning(f"No data received from {source_name}")
                except Exception as e:
                    logger.error(f"Error collecting data from {source_name}: {str(e)}")
        
        return source_data
    
    def _collect_from_source(self, source_name: str, service: Any, 
                           search_params: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Collect data from a specific source
        
        Args:
            source_name: Name of the source
            service: Service instance
            search_params: Search parameters
            
        Returns:
            Data from the source or None if failed
        """
        try:
            name = search_params['name']
            
            if source_name == 'wikipedia':
                return service.get_person_data(name)
            elif source_name == 'news':
                return service.get_recent_news(name, days=90)
            else:
                # For future sources
                return None
                
        except Exception as e:
            logger.error(f"Error collecting from {source_name}: {str(e)}")
            return None
    
    def _aggregate_data(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aggregate data from multiple sources into a unified format
        
        Args:
            source_data: Data from all sources
            
        Returns:
            Aggregated data dictionary
        """
        aggregated = {
            'name': {},
            'personal_info': {},
            'family_info': {},
            'education': [],
            'work_history': [],
            'connections': [],
            'interests': [],
            'investments': [],
            'financial_info': {},
            'source_details': source_data
        }
        
        # Process Wikipedia data
        if 'wikipedia' in source_data:
            wiki_data = source_data['wikipedia']
            aggregated = self._merge_wikipedia_data(aggregated, wiki_data)
        
        # Process News data
        if 'news' in source_data:
            news_data = source_data['news']
            aggregated = self._merge_news_data(aggregated, news_data)
        
        # Process other sources as they become available
        # ...
        
        return aggregated
    
    def _merge_wikipedia_data(self, aggregated: Dict[str, Any], 
                            wiki_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge Wikipedia data into aggregated structure
        
        Args:
            aggregated: Current aggregated data
            wiki_data: Wikipedia data
            
        Returns:
            Updated aggregated data
        """
        # Name information
        if 'name' in wiki_data:
            aggregated['name'] = {
                'full_name': wiki_data['name'],
                'aliases': wiki_data.get('aliases', [])
            }
        
        # Personal information
        if 'personal_info' in wiki_data:
            personal = wiki_data['personal_info']
            aggregated['personal_info'].update({
                'date_of_birth': personal.get('birth_date', ''),
                'age': personal.get('age', ''),
                'birth_year': personal.get('birth_year', ''),
                'nationality': personal.get('nationality', ''),
                'occupation': personal.get('occupation', '')
            })
        
        # Family information
        if 'family' in wiki_data:
            family = wiki_data['family']
            aggregated['family_info'] = {
                'spouse': family.get('spouse', {}),
                'children': family.get('children', []),
                'parents': family.get('parents', []),
                'siblings': family.get('siblings', [])
            }
        
        # Education
        if 'education' in wiki_data:
            for edu in wiki_data['education']:
                aggregated['education'].append({
                    'institution': edu.get('institution', ''),
                    'degree': edu.get('degree', ''),
                    'year': edu.get('year', ''),
                    'source': 'wikipedia'
                })
        
        # Work history
        if 'career' in wiki_data:
            for job in wiki_data['career']:
                aggregated['work_history'].append({
                    'title': job.get('title', ''),
                    'company': job.get('company', ''),
                    'duration': job.get('duration', ''),
                    'description': job.get('description', ''),
                    'source': 'wikipedia'
                })
        
        return aggregated
    
    def _merge_news_data(self, aggregated: Dict[str, Any], 
                        news_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge news data into aggregated structure
        
        Args:
            aggregated: Current aggregated data
            news_data: News data
            
        Returns:
            Updated aggregated data
        """
        # Extract additional information from news articles
        if 'articles' in news_data:
            for article in news_data['articles']:
                # Extract company mentions
                if 'company_mentions' in article:
                    for company in article['company_mentions']:
                        # Check if this adds new work history
                        existing_companies = [job.get('company', '') for job in aggregated['work_history']]
                        if company not in existing_companies:
                            aggregated['work_history'].append({
                                'company': company,
                                'source': 'news',
                                'confidence': 'low'  # News mentions are less reliable
                            })
                
                # Extract connections from article content
                if 'connections' in article:
                    for connection in article['connections']:
                        aggregated['connections'].append({
                            'name': connection.get('name', ''),
                            'type': connection.get('type', 'professional'),
                            'source': 'news'
                        })
        
        return aggregated
    
    def _deduplicate_and_rank_search_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicates and rank search results
        
        Args:
            results: List of search results
            
        Returns:
            Deduplicated and ranked results
        """
        # Simple deduplication based on name similarity
        unique_results = []
        seen_names = set()
        
        for result in results:
            name = result.get('name', '').lower()
            if name not in seen_names:
                seen_names.add(name)
                unique_results.append(result)
        
        # Rank by relevance score (if available) or source weight
        def get_rank_score(result):
            source_weight = self.sources.get(result.get('source', ''), {}).get('weight', 0)
            relevance_score = result.get('relevance_score', 0.5)
            return source_weight * relevance_score
        
        unique_results.sort(key=get_rank_score, reverse=True)
        
        return unique_results[:10]  # Return top 10 results