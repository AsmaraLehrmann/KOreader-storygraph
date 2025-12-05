#!/usr/bin/env python3
"""
Test script for StoryGraph Sync
Simulates a manual sync with sample data
"""

import requests
import json
import sys

def test_sync(service_url):
    """Test the sync endpoint with sample data"""
    
    # Sample book data
    test_data = {
        "books": [
            {
                "title": "Project Hail Mary",
                "author": "Andy Weir",
                "current_page": 234,
                "total_pages": 476,
                "progress": 49.2
            },
            {
                "title": "The Martian",
                "author": "Andy Weir",
                "current_page": 150,
                "total_pages": 369,
                "progress": 40.7
            }
        ]
    }
    
    print(f"🧪 Testing StoryGraph Sync at {service_url}")
    print(f"📚 Sending {len(test_data['books'])} test books...")
    print()
    
    try:
        # Test health check first
        print("1️⃣  Testing health check endpoint...")
        response = requests.get(service_url)
        response.raise_for_status()
        print(f"   ✅ Health check passed: {response.json()}")
        print()
        
        # Test manual sync
        print("2️⃣  Testing manual sync endpoint...")
        response = requests.post(
            f"{service_url}/manual-sync",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        
        result = response.json()
        print(f"   ✅ Sync completed!")
        print(f"   📊 Results:")
        print(json.dumps(result, indent=2))
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error: {e}")
        if hasattr(e.response, 'text'):
            print(f"   Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python test.py <service-url>")
        print("Example: python test.py https://storygraph-sync-xxx.run.app")
        sys.exit(1)
    
    service_url = sys.argv[1].rstrip('/')
    
    success = test_sync(service_url)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
