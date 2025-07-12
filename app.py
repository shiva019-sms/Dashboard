from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our custom modules
from services.data_aggregator import DataAggregator
from services.wikipedia_service import WikipediaService
from services.news_service import NewsService
from models.promoter_profile import PromoterProfile
from utils.validation import validate_person_name
from utils.logging_config import setup_logging

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize services
wikipedia_service = WikipediaService()
news_service = NewsService()
data_aggregator = DataAggregator()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/v1/promoter-details', methods=['POST'])
def get_promoter_details():
    """
    Get comprehensive promoter details for a high-profile individual
    
    Expected JSON payload:
    {
        "name": "John Doe",
        "title": "CEO",  # optional
        "company": "Example Corp",  # optional
        "context": "additional context"  # optional
    }
    """
    try:
        # Validate request
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        
        # Validate required fields
        if not data or 'name' not in data:
            return jsonify({'error': 'Name is required'}), 400
        
        name = data['name'].strip()
        if not validate_person_name(name):
            return jsonify({'error': 'Invalid name format'}), 400
        
        # Extract optional fields
        title = data.get('title', '').strip()
        company = data.get('company', '').strip()
        context = data.get('context', '').strip()
        
        logger.info(f"Processing promoter details request for: {name}")
        
        # Aggregate data from multiple sources
        profile_data = data_aggregator.gather_comprehensive_data(
            name=name,
            title=title,
            company=company,
            context=context
        )
        
        # Create structured promoter profile
        promoter_profile = PromoterProfile(profile_data)
        
        # Return structured response
        return jsonify({
            'status': 'success',
            'data': promoter_profile.to_dict(),
            'sources': profile_data.get('sources', []),
            'confidence_score': profile_data.get('confidence_score', 0.0),
            'last_updated': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error processing promoter details request: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/api/v1/search', methods=['POST'])
def search_person():
    """
    Search for a person and return basic information
    
    Expected JSON payload:
    {
        "query": "Elon Musk CEO Tesla"
    }
    """
    try:
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({'error': 'Query is required'}), 400
        
        query = data['query'].strip()
        
        logger.info(f"Processing search request for: {query}")
        
        # Search for person using multiple sources
        search_results = data_aggregator.search_person(query)
        
        return jsonify({
            'status': 'success',
            'results': search_results,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error processing search request: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/api/v1/wikipedia/<path:person_name>', methods=['GET'])
def get_wikipedia_data(person_name):
    """Get Wikipedia data for a specific person"""
    try:
        logger.info(f"Fetching Wikipedia data for: {person_name}")
        
        wikipedia_data = wikipedia_service.get_person_data(person_name)
        
        if not wikipedia_data:
            return jsonify({
                'status': 'not_found',
                'message': f'No Wikipedia data found for {person_name}'
            }), 404
        
        return jsonify({
            'status': 'success',
            'data': wikipedia_data,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error fetching Wikipedia data: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/api/v1/news/<path:person_name>', methods=['GET'])
def get_news_data(person_name):
    """Get recent news data for a specific person"""
    try:
        logger.info(f"Fetching news data for: {person_name}")
        
        # Get query parameters
        days = request.args.get('days', 30, type=int)
        limit = request.args.get('limit', 10, type=int)
        
        news_data = news_service.get_recent_news(person_name, days=days, limit=limit)
        
        return jsonify({
            'status': 'success',
            'data': news_data,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error fetching news data: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/api/v1/sources', methods=['GET'])
def get_available_sources():
    """Get list of available data sources and their status"""
    try:
        sources_status = data_aggregator.get_sources_status()
        
        return jsonify({
            'status': 'success',
            'sources': sources_status,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error fetching sources status: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'message': 'The requested endpoint does not exist'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    logger.info(f"Starting Promoter Details Agent on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)