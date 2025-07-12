#!/usr/bin/env python3
"""
Example test script for the Promoter Details Agent

This script demonstrates how to use the API to gather information
about high-profile individuals.
"""

import requests
import json
import time
from typing import Dict, Any, Optional

# Configuration
API_BASE_URL = "http://localhost:5000"
TIMEOUT = 30

def test_health_check():
    """Test the health check endpoint"""
    print("Testing health check...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Health check passed: {data['status']}")
            return True
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Health check error: {str(e)}")
        return False

def get_promoter_details(name: str, title: str = "", company: str = "") -> Optional[Dict[str, Any]]:
    """Get promoter details for a person"""
    print(f"\nGetting promoter details for: {name}")
    
    payload = {
        "name": name,
        "title": title,
        "company": company
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/promoter-details",
            json=payload,
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                print(f"✓ Successfully retrieved data for {name}")
                return data
            else:
                print(f"✗ API returned error: {data.get('error', 'Unknown error')}")
                return None
        else:
            print(f"✗ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.RequestException as e:
        print(f"✗ Request error: {str(e)}")
        return None

def display_promoter_details(data: Dict[str, Any]):
    """Display promoter details in a formatted way"""
    details = data['data']['promoter_details']
    metadata = data['data']['metadata']
    
    print("\n" + "="*80)
    print("PROMOTER DETAILS REPORT")
    print("="*80)
    
    print(f"Name: {details['name']}")
    print(f"DOB/Age: {details['dob_age']}")
    print(f"Spouse: {details['spouse_name_and_age']}")
    print(f"Children: {', '.join(details['children_names_and_ages'])}")
    
    print(f"\nEducational Background:")
    for edu in details['educational_background']:
        print(f"  • {edu}")
    
    print(f"\nProfessional Background:")
    for work in details['professional_background']:
        print(f"  • {work}")
    
    print(f"\nPrivate Banker: {details['private_banker']}")
    print(f"ICICI Bank Relationship: {details['icici_bank_relationship']}")
    
    print(f"\nKey Connections:")
    for category, connections in details['key_connections'].items():
        print(f"  {category.replace('_', ' ').title()}:")
        for connection in connections[:3]:  # Show first 3
            print(f"    - {connection}")
    
    print(f"\nAreas of Interest/Investments:")
    for interest in details['area_of_interest_investments'][:5]:  # Show first 5
        print(f"  • {interest}")
    
    print(f"\nMetadata:")
    print(f"  Confidence Score: {metadata['confidence_score']}")
    print(f"  Sources Used: {', '.join(metadata['sources_used'])}")
    print(f"  Last Updated: {metadata['last_updated']}")
    
    print("="*80)

def test_search(query: str):
    """Test the search endpoint"""
    print(f"\nTesting search for: {query}")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/search",
            json={"query": query},
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                results = data['results']
                print(f"✓ Found {len(results)} search results")
                for i, result in enumerate(results[:3]):  # Show first 3
                    print(f"  {i+1}. {result.get('name', 'Unknown')} - {result.get('description', '')[:100]}...")
                return True
            else:
                print(f"✗ Search failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"✗ Search request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Search error: {str(e)}")
        return False

def test_wikipedia_endpoint(name: str):
    """Test the Wikipedia endpoint"""
    print(f"\nTesting Wikipedia data for: {name}")
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/wikipedia/{name}",
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                print(f"✓ Wikipedia data retrieved for {name}")
                return True
            else:
                print(f"✗ Wikipedia lookup failed: {data.get('message', 'Unknown error')}")
                return False
        else:
            print(f"✗ Wikipedia request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Wikipedia error: {str(e)}")
        return False

def test_sources_status():
    """Test the sources status endpoint"""
    print("\nTesting sources status...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/sources", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                sources = data['sources']
                print("✓ Sources status retrieved:")
                for source, info in sources.items():
                    status = info['status']
                    enabled = info['enabled']
                    print(f"  {source}: {status} ({'enabled' if enabled else 'disabled'})")
                return True
            else:
                print(f"✗ Sources status failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"✗ Sources status request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Sources status error: {str(e)}")
        return False

def main():
    """Run the test suite"""
    print("Promoter Details Agent - Test Suite")
    print("=" * 50)
    
    # Test cases
    test_cases = [
        {"name": "Elon Musk", "title": "CEO", "company": "Tesla"},
        {"name": "Tim Cook", "title": "CEO", "company": "Apple"},
        {"name": "Satya Nadella", "title": "CEO", "company": "Microsoft"},
    ]
    
    # Start with health check
    if not test_health_check():
        print("Health check failed. Make sure the API is running at", API_BASE_URL)
        return
    
    # Test sources status
    test_sources_status()
    
    # Test search functionality
    test_search("Sundar Pichai CEO Google")
    
    # Test Wikipedia endpoint
    test_wikipedia_endpoint("Elon Musk")
    
    # Test promoter details for each case
    print(f"\n{'='*50}")
    print("TESTING PROMOTER DETAILS ENDPOINT")
    print('='*50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[Test Case {i}]")
        
        data = get_promoter_details(
            name=test_case["name"],
            title=test_case["title"],
            company=test_case["company"]
        )
        
        if data:
            display_promoter_details(data)
        else:
            print(f"✗ Failed to get data for {test_case['name']}")
        
        # Add delay between requests to be respectful
        if i < len(test_cases):
            print("\nWaiting 5 seconds before next request...")
            time.sleep(5)
    
    print(f"\n{'='*50}")
    print("TEST SUITE COMPLETED")
    print('='*50)

if __name__ == "__main__":
    main()