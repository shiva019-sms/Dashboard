# Promoter Details Agent

A comprehensive API system for gathering detailed information about high-profile individuals (CEOs, CFOs, COOs, etc.) from multiple public sources and presenting it in a structured promoter details format suitable for financial due diligence.

## Features

- **Multi-Source Data Aggregation**: Combines information from Wikipedia, news sources, and other public APIs
- **Structured Output**: Formats data according to promoter details requirements including:
  - Personal Information (Name, DOB/Age, Family)
  - Educational Background
  - Professional Background
  - Key Connections
  - Areas of Interest/Investments
- **Confidence Scoring**: Provides reliability scores for all gathered information
- **Real-time Processing**: Fetches and processes data on-demand
- **Privacy Compliant**: Only uses publicly available information
- **Extensible Architecture**: Easy to add new data sources

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Flask API     │    │  Data Aggregator │    │  Data Sources   │
│                 │────│                  │────│                 │
│ • REST Endpoints│    │ • Source Manager │    │ • Wikipedia     │
│ • Validation    │    │ • Data Merger    │    │ • News APIs     │
│ • Error Handling│    │ • Confidence     │    │ • Future APIs   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         v                       v                       v
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Promoter Profile│    │   Utilities      │    │    Logging      │
│                 │    │                  │    │                 │
│ • Structured    │    │ • Data Processor │    │ • File & Console│
│   Output Format │    │ • Validation     │    │ • Error Tracking│
│ • Field Mapping │    │ • Confidence Calc│    │ • Audit Trail   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd promoter-details-agent
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

5. **Run the application**:
   ```bash
   python app.py
   ```

The API will be available at `http://localhost:5000`

## API Endpoints

### Health Check
```http
GET /health
```
Returns the health status of the application.

### Get Promoter Details
```http
POST /api/v1/promoter-details
Content-Type: application/json

{
  "name": "Elon Musk",
  "title": "CEO",
  "company": "Tesla",
  "context": "Technology executive"
}
```

**Response**:
```json
{
  "status": "success",
  "data": {
    "promoter_details": {
      "name": "Elon Musk",
      "dob_age": "DOB: June 28, 1971 (Age: 52)",
      "spouse_name_and_age": "Not available",
      "children_names_and_ages": ["X Æ A-XII", "Griffin Musk", "..."],
      "educational_background": ["Bachelor's degree from University of Pennsylvania"],
      "professional_background": ["CEO at Tesla", "CEO at SpaceX", "..."],
      "private_banker": "Not available",
      "icici_bank_relationship": "Not available",
      "key_connections": {
        "family": ["..."],
        "friends": ["..."],
        "professional": ["..."],
        "social_network": ["..."]
      },
      "area_of_interest_investments": ["Electric vehicles", "Space exploration", "..."]
    },
    "metadata": {
      "confidence_score": 0.85,
      "sources_used": ["wikipedia", "news"],
      "last_updated": "2024-01-15T10:30:00Z"
    }
  },
  "sources": ["wikipedia", "news"],
  "confidence_score": 0.85,
  "last_updated": "2024-01-15T10:30:00Z"
}
```

### Search Person
```http
POST /api/v1/search
Content-Type: application/json

{
  "query": "Sundar Pichai CEO Google"
}
```

### Get Wikipedia Data
```http
GET /api/v1/wikipedia/{person_name}
```

### Get News Data
```http
GET /api/v1/news/{person_name}?days=30&limit=10
```

### Get Sources Status
```http
GET /api/v1/sources
```

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `FLASK_ENV` | Flask environment | No | `development` |
| `PORT` | Port to run the application | No | `5000` |
| `LOG_LEVEL` | Logging level | No | `INFO` |
| `NEWS_API_KEY` | NewsAPI key for news data | No | - |
| `PDL_API_KEY` | People Data Labs API key | No | - |

### Data Sources

The system currently supports:

1. **Wikipedia** (Free, always available)
   - Biographical information
   - Career history
   - Education details
   - Family information

2. **News APIs** (Optional, requires API key)
   - Recent news articles
   - Professional activities
   - Company mentions
   - Public statements

3. **Future Sources** (Planned)
   - Crunchbase (business information)
   - LinkedIn (professional networks)
   - SEC filings (public company executives)

## Data Privacy and Compliance

### Privacy Principles

- **Public Information Only**: Only gathers information that is publicly available
- **No Personal Contact**: Does not collect private contact information
- **Transparent Sources**: All data sources are clearly attributed
- **Consent Respect**: Respects robots.txt and API terms of service

### Legal Considerations

- **GDPR Compliance**: System design considers data protection requirements
- **Terms of Service**: All API usage complies with provider terms
- **Fair Use**: Implements rate limiting and respectful data collection
- **Data Retention**: Implements appropriate data retention policies

### Ethical Guidelines

- **Legitimate Purpose**: Designed for legitimate business due diligence
- **Accuracy**: Provides confidence scores and source attribution
- **Transparency**: Clear about data sources and limitations
- **No Harm**: Avoids collection of sensitive personal information

## Confidence Scoring

The system provides confidence scores (0.0 to 1.0) based on:

- **Source Quality** (30%): Reliability of data sources
- **Data Completeness** (35%): How much information is available
- **Data Consistency** (25%): Agreement between sources
- **Data Freshness** (10%): How recent the information is

### Confidence Levels

- **0.8 - 1.0**: High confidence - Multiple reliable sources
- **0.6 - 0.8**: Medium confidence - Some verification needed
- **0.4 - 0.6**: Low confidence - Limited or conflicting sources
- **0.0 - 0.4**: Very low confidence - Insufficient or unreliable data

## Usage Examples

### Basic Usage

```python
import requests

# Get promoter details
response = requests.post('http://localhost:5000/api/v1/promoter-details', 
                        json={'name': 'Tim Cook'})
data = response.json()

if data['status'] == 'success':
    promoter_details = data['data']['promoter_details']
    confidence = data['confidence_score']
    print(f"Confidence: {confidence}")
    print(f"Name: {promoter_details['name']}")
    print(f"Age: {promoter_details['dob_age']}")
    print(f"Education: {promoter_details['educational_background']}")
```

### Advanced Usage with Error Handling

```python
import requests
from typing import Optional, Dict, Any

def get_promoter_details(name: str, title: str = '', 
                        company: str = '') -> Optional[Dict[str, Any]]:
    """Get promoter details with error handling"""
    try:
        response = requests.post(
            'http://localhost:5000/api/v1/promoter-details',
            json={
                'name': name,
                'title': title,
                'company': company
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                return data['data']
        
        return None
        
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return None

# Usage
details = get_promoter_details('Satya Nadella', 'CEO', 'Microsoft')
if details:
    print(f"Confidence: {details['metadata']['confidence_score']}")
else:
    print("Failed to retrieve details")
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Format code
black .

# Lint code
flake8 .
```

### Adding New Data Sources

1. Create a new service in `services/` directory
2. Implement the required interface methods:
   - `health_check()`
   - `search_person(query)`
   - `get_person_data(name)`
3. Update `DataAggregator` to include the new source
4. Add source weight in `ConfidenceCalculator`

### Example: Adding a new service

```python
# services/example_service.py
class ExampleService:
    def health_check(self) -> bool:
        # Check if service is available
        return True
    
    def search_person(self, query: str) -> List[Dict[str, Any]]:
        # Search for person
        return []
    
    def get_person_data(self, name: str) -> Optional[Dict[str, Any]]:
        # Get detailed person data
        return None
```

## Monitoring and Logging

### Log Files

- `logs/promoter_agent_YYYYMMDD.log`: Application logs
- `logs/errors.log`: Error logs only

### Monitoring Endpoints

- `/health`: Application health status
- `/api/v1/sources`: Data source status

## Troubleshooting

### Common Issues

1. **"No data found" errors**:
   - Check if the person name is spelled correctly
   - Try variations of the name
   - Check if the person has a Wikipedia page

2. **Rate limiting errors**:
   - The system respects rate limits of external APIs
   - Wait before making additional requests
   - Consider upgrading API plans for higher limits

3. **Low confidence scores**:
   - May indicate limited public information
   - Try different name variations
   - Add more context (title, company)

### Debug Mode

Set `FLASK_ENV=development` and `LOG_LEVEL=DEBUG` for detailed logging.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This system is designed for legitimate business purposes such as financial due diligence. Users are responsible for:

- Ensuring compliance with applicable laws and regulations
- Respecting the privacy rights of individuals
- Using the information ethically and responsibly
- Verifying information from primary sources when needed

The accuracy and completeness of information cannot be guaranteed, as it depends on the availability and accuracy of public sources.