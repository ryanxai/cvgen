#!/usr/bin/env python3

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_improve_summary():
    """Test the improve-summary endpoint"""
    
    # API endpoint URL (adjust if running on different port/host)
    base_url = "http://localhost:8000"
    
    # Test data
    test_data = {
        "instructions": "You are a professional recruiter. Improve the writing style of the following summary section to be more professional and concise. Don't provide any other text than the improved summary section.",
        "summary": "Senior Data Scientist and ML Engineer with 10+ years of expertise in NLP, speech processing, and generative AI. Demonstrated success developing LLM-based systems achieving high accuracy metrics. Specialized in building end-to-end AI solutions from concept to production, combining deep learning architectures with practical business applications for start-ups and big companies."
    }
    
    try:
        # Make the API call
        response = requests.post(
            f"{base_url}/improve-summary",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Success!")
            print(f"Message: {result['message']}")
            print(f"Improved Summary:\n{result['improved_summary']}")
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the API server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_health_check():
    """Test the health check endpoint to verify the server is running"""
    
    base_url = "http://localhost:8000"
    
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Health Check Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Server is running and healthy")
            return True
        else:
            print("❌ Server health check failed")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running on http://localhost:8000")
        return False

if __name__ == "__main__":
    print("Testing Resume Builder API - Improve Summary Endpoint")
    print("=" * 60)
    
    # First check if server is running
    if test_health_check():
        print("\n" + "=" * 60)
        test_improve_summary()
    else:
        print("\nPlease start the server first with: python main.py") 