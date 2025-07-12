import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import re
import os
from urllib.parse import quote

logger = logging.getLogger(__name__)

class NewsService:
    """
    Service for gathering recent news and information about individuals
    """
    
    def __init__(self):
        self.news_api_key = os.getenv('NEWS_API_KEY', '')
        self.newsapi_base_url = "https://newsapi.org/v2"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PromoterDetailsAgent/1.0',
            'X-API-Key': self.news_api_key
        })
        
        # Alternative free news sources
        self.alternative_sources = [
            'https://rss.cnn.com/rss/edition.rss',
            'https://feeds.reuters.com/reuters/businessNews',
            'https://feeds.bbci.co.uk/news/business/rss.xml'
        ]
    
    def health_check(self) -> bool:
        """
        Check if news services are accessible
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            if self.news_api_key:
                # Test NewsAPI
                response = self.session.get(
                    f"{self.newsapi_base_url}/top-headlines",
                    params={
                        'country': 'us',
                        'pageSize': 1
                    },
                    timeout=10
                )
                return response.status_code == 200
            else:
                # Test alternative sources (basic connectivity)
                response = requests.get(
                    "https://www.google.com",
                    timeout=10
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"News service health check failed: {str(e)}")
            return False
    
    def search_person(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for a person in news articles
        
        Args:
            query: Search query
            
        Returns:
            List of search results
        """
        try:
            if self.news_api_key:
                return self._search_with_newsapi(query)
            else:
                return self._search_with_google_news(query)
        except Exception as e:
            logger.error(f"News search failed: {str(e)}")
            return []
    
    def get_recent_news(self, person_name: str, days: int = 30, 
                       limit: int = 10) -> Dict[str, Any]:
        """
        Get recent news articles about a person
        
        Args:
            person_name: Name of the person
            days: Number of days to look back
            limit: Maximum number of articles to return
            
        Returns:
            Dictionary containing news articles and analysis
        """
        try:
            articles = []
            
            if self.news_api_key:
                articles = self._get_newsapi_articles(person_name, days, limit)
            else:
                articles = self._get_alternative_news(person_name, days, limit)
            
            # Analyze articles for additional information
            analysis = self._analyze_news_articles(articles, person_name)
            
            return {
                'articles': articles,
                'analysis': analysis,
                'total_articles': len(articles),
                'date_range': f"{days} days",
                'person_name': person_name,
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting recent news for {person_name}: {str(e)}")
            return {
                'articles': [],
                'analysis': {},
                'total_articles': 0,
                'error': str(e)
            }
    
    def _search_with_newsapi(self, query: str) -> List[Dict[str, Any]]:
        """Search using NewsAPI"""
        try:
            response = self.session.get(
                f"{self.newsapi_base_url}/everything",
                params={
                    'q': query,
                    'sortBy': 'relevancy',
                    'pageSize': 10,
                    'language': 'en'
                },
                timeout=15
            )
            
            if response.status_code != 200:
                logger.error(f"NewsAPI search failed with status {response.status_code}")
                return []
            
            data = response.json()
            
            if data.get('status') != 'ok':
                logger.error(f"NewsAPI error: {data.get('message', 'Unknown error')}")
                return []
            
            results = []
            for article in data.get('articles', []):
                results.append({
                    'name': self._extract_person_name(article.get('title', '')),
                    'title': article.get('title', ''),
                    'description': article.get('description', ''),
                    'url': article.get('url', ''),
                    'source': article.get('source', {}).get('name', ''),
                    'published_date': article.get('publishedAt', ''),
                    'relevance_score': 0.8  # High relevance for exact matches
                })
            
            return results
            
        except Exception as e:
            logger.error(f"NewsAPI search failed: {str(e)}")
            return []
    
    def _search_with_google_news(self, query: str) -> List[Dict[str, Any]]:
        """Search using Google News RSS (free alternative)"""
        try:
            # Use Google News RSS feed
            encoded_query = quote(query)
            url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
            
            response = requests.get(url, timeout=15)
            if response.status_code != 200:
                return []
            
            # Parse RSS feed
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            
            results = []
            for item in root.findall('.//item')[:10]:  # Limit to 10 results
                title = item.find('title')
                link = item.find('link')
                description = item.find('description')
                pub_date = item.find('pubDate')
                
                if title is not None and link is not None:
                    results.append({
                        'name': self._extract_person_name(title.text or ''),
                        'title': title.text or '',
                        'description': description.text or '' if description is not None else '',
                        'url': link.text or '',
                        'source': 'Google News',
                        'published_date': pub_date.text or '' if pub_date is not None else '',
                        'relevance_score': 0.6  # Medium relevance for RSS results
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Google News search failed: {str(e)}")
            return []
    
    def _get_newsapi_articles(self, person_name: str, days: int, 
                            limit: int) -> List[Dict[str, Any]]:
        """Get articles using NewsAPI"""
        try:
            # Calculate date range
            from_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            response = self.session.get(
                f"{self.newsapi_base_url}/everything",
                params={
                    'q': f'"{person_name}"',
                    'from': from_date,
                    'sortBy': 'publishedAt',
                    'pageSize': limit,
                    'language': 'en'
                },
                timeout=15
            )
            
            if response.status_code != 200:
                logger.error(f"NewsAPI failed with status {response.status_code}")
                return []
            
            data = response.json()
            
            if data.get('status') != 'ok':
                logger.error(f"NewsAPI error: {data.get('message', 'Unknown error')}")
                return []
            
            articles = []
            for article in data.get('articles', []):
                articles.append({
                    'title': article.get('title', ''),
                    'description': article.get('description', ''),
                    'content': article.get('content', ''),
                    'url': article.get('url', ''),
                    'source': article.get('source', {}).get('name', ''),
                    'published_date': article.get('publishedAt', ''),
                    'url_to_image': article.get('urlToImage', ''),
                    'author': article.get('author', '')
                })
            
            return articles
            
        except Exception as e:
            logger.error(f"NewsAPI articles fetch failed: {str(e)}")
            return []
    
    def _get_alternative_news(self, person_name: str, days: int, 
                            limit: int) -> List[Dict[str, Any]]:
        """Get articles using alternative free sources"""
        try:
            # Use Google News RSS as fallback
            encoded_query = quote(f'"{person_name}"')
            url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
            
            response = requests.get(url, timeout=15)
            if response.status_code != 200:
                return []
            
            # Parse RSS feed
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            
            articles = []
            for item in root.findall('.//item')[:limit]:
                title = item.find('title')
                link = item.find('link')
                description = item.find('description')
                pub_date = item.find('pubDate')
                
                if title is not None and link is not None:
                    # Check if article is within date range
                    if pub_date is not None and pub_date.text:
                        try:
                            from dateutil import parser
                            article_date = parser.parse(pub_date.text)
                            cutoff_date = datetime.now(article_date.tzinfo) - timedelta(days=days)
                            
                            if article_date < cutoff_date:
                                continue
                        except:
                            pass  # If date parsing fails, include the article
                    
                    articles.append({
                        'title': title.text or '',
                        'description': description.text or '' if description is not None else '',
                        'content': '',  # Not available in RSS
                        'url': link.text or '',
                        'source': 'Google News',
                        'published_date': pub_date.text or '' if pub_date is not None else '',
                        'url_to_image': '',
                        'author': ''
                    })
            
            return articles
            
        except Exception as e:
            logger.error(f"Alternative news fetch failed: {str(e)}")
            return []
    
    def _analyze_news_articles(self, articles: List[Dict[str, Any]], 
                             person_name: str) -> Dict[str, Any]:
        """
        Analyze news articles to extract additional information
        
        Args:
            articles: List of news articles
            person_name: Name of the person
            
        Returns:
            Dictionary containing analysis results
        """
        analysis = {
            'company_mentions': [],
            'connections': [],
            'recent_activities': [],
            'sentiment_indicators': [],
            'key_topics': []
        }
        
        try:
            for article in articles:
                title = article.get('title', '')
                description = article.get('description', '')
                content = article.get('content', '')
                
                # Combine all text for analysis
                text = f"{title} {description} {content}".lower()
                
                # Extract company mentions
                companies = self._extract_company_mentions(text)
                for company in companies:
                    if company not in analysis['company_mentions']:
                        analysis['company_mentions'].append(company)
                
                # Extract connections (people mentioned with the person)
                connections = self._extract_person_connections(text, person_name)
                analysis['connections'].extend(connections)
                
                # Extract recent activities
                activities = self._extract_activities(text)
                analysis['recent_activities'].extend(activities)
                
                # Basic sentiment analysis
                sentiment = self._analyze_sentiment(text)
                if sentiment:
                    analysis['sentiment_indicators'].append({
                        'article_title': title,
                        'sentiment': sentiment,
                        'date': article.get('published_date', '')
                    })
                
                # Extract key topics
                topics = self._extract_key_topics(text)
                analysis['key_topics'].extend(topics)
            
            # Remove duplicates and limit results
            analysis['company_mentions'] = list(set(analysis['company_mentions']))[:10]
            analysis['connections'] = self._deduplicate_connections(analysis['connections'])[:10]
            analysis['recent_activities'] = analysis['recent_activities'][:10]
            analysis['key_topics'] = list(set(analysis['key_topics']))[:10]
            
        except Exception as e:
            logger.error(f"News analysis failed: {str(e)}")
        
        return analysis
    
    def _extract_person_name(self, text: str) -> str:
        """Extract person name from text"""
        # Simple extraction - look for capitalized words
        words = text.split()
        names = []
        
        for word in words:
            if word[0].isupper() and len(word) > 1:
                names.append(word)
        
        return ' '.join(names[:3])  # Return first 3 capitalized words
    
    def _extract_company_mentions(self, text: str) -> List[str]:
        """Extract company mentions from text"""
        # Common company indicators
        company_indicators = [
            r'(\w+)\s+(?:Inc\.|Corporation|Corp\.|Company|Ltd\.|LLC)',
            r'(\w+)\s+(?:Technologies|Systems|Solutions|Services)',
            r'(\w+)\s+(?:Bank|Financial|Insurance|Motors|Airlines)'
        ]
        
        companies = []
        for pattern in company_indicators:
            matches = re.findall(pattern, text, re.IGNORECASE)
            companies.extend(matches)
        
        return companies
    
    def _extract_person_connections(self, text: str, person_name: str) -> List[Dict[str, Any]]:
        """Extract people mentioned in connection with the person"""
        connections = []
        
        # Look for patterns like "John Smith and Jane Doe"
        # This is a simplified approach
        name_pattern = r'([A-Z][a-z]+\s+[A-Z][a-z]+)'
        names = re.findall(name_pattern, text)
        
        for name in names:
            if name.lower() != person_name.lower():
                connections.append({
                    'name': name,
                    'type': 'mentioned_with',
                    'context': 'news_article'
                })
        
        return connections
    
    def _extract_activities(self, text: str) -> List[str]:
        """Extract recent activities from text"""
        activity_patterns = [
            r'(appointed|hired|promoted|joined|left|resigned|founded|launched|announced|signed|acquired|sold|invested)',
            r'(will|plans to|expected to|scheduled to)'
        ]
        
        activities = []
        for pattern in activity_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            activities.extend(matches)
        
        return activities
    
    def _analyze_sentiment(self, text: str) -> str:
        """Basic sentiment analysis"""
        positive_words = ['success', 'growth', 'profit', 'achievement', 'win', 'positive', 'good', 'excellent']
        negative_words = ['loss', 'decline', 'failure', 'problem', 'issue', 'negative', 'bad', 'poor']
        
        positive_count = sum(1 for word in positive_words if word in text.lower())
        negative_count = sum(1 for word in negative_words if word in text.lower())
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def _extract_key_topics(self, text: str) -> List[str]:
        """Extract key topics from text"""
        # Common business/executive topics
        topics = [
            'merger', 'acquisition', 'ipo', 'funding', 'investment',
            'leadership', 'strategy', 'revenue', 'growth', 'expansion',
            'technology', 'innovation', 'market', 'competition'
        ]
        
        found_topics = []
        for topic in topics:
            if topic in text.lower():
                found_topics.append(topic)
        
        return found_topics
    
    def _deduplicate_connections(self, connections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate connections"""
        seen = set()
        unique_connections = []
        
        for connection in connections:
            name = connection.get('name', '').lower()
            if name not in seen:
                seen.add(name)
                unique_connections.append(connection)
        
        return unique_connections