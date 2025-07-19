#!/usr/bin/env python3
"""
Test script for the Resume Builder FastAPI
This script demonstrates how to use the different API endpoints
"""

import requests
import json
import yaml
from typing import Dict, Any

# Default API base URL
API_BASE = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint"""
    print("Testing health check...")
    response = requests.get(f"{API_BASE}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print("-" * 50)

def test_sample_data():
    """Get sample data structure"""
    print("Getting sample data structure...")
    response = requests.get(f"{API_BASE}/sample-data")
    if response.status_code == 200:
        print(f"Status: {response.status_code}")
        sample_data = response.json()["sample_data"]
        print("Sample data structure retrieved successfully")
        return sample_data
    else:
        print(f"Failed to get sample data: {response.status_code}")
        return None

def test_generate_resume_json(sample_data: Dict[Any, Any] = None):
    """Test generating resume with JSON data"""
    print("Testing resume generation with JSON data...")
    
    if sample_data is None:
        # Use simplified test data if no sample available
        test_data = {
            "name": "Test User API",
            "contact": {
                "phone": "+1 (555) 999-8888",
                "email": "test.api@example.com",
                "location": "API City, AC, United States",
                "links": [
                    {"name": "GitHub", "url": "https://github.com/testuser"},
                    {"name": "LinkedIn", "url": "https://linkedin.com/in/testuser"}
                ]
            },
            "summary": "API Test Resume - Testing FastAPI resume generation functionality",
            "skills": [
                {"category": "Programming", "items": "Python, JavaScript, FastAPI, REST APIs"},
                {"category": "Tools", "items": "Docker, Git, LaTeX"}
            ],
            "experience": [
                {
                    "title": "API Developer",
                    "company": "Test Corp",
                    "location": "Remote",
                    "date_start": "Jan 2023",
                    "date_end": "Present",
                    "achievements": [
                        {
                            "name": "FastAPI Implementation",
                            "description": "Successfully implemented FastAPI for resume generation service"
                        }
                    ]
                }
            ],
            "education": [
                {
                    "degree": "B.S. in Computer Science",
                    "institution": "API University",
                    "location": "Test City, TC",
                    "date_start": "2019",
                    "date_end": "2023"
                }
            ],
            "awards": [],
            "certifications": [],
            "publications": []
        }
    else:
        test_data = sample_data
        # Modify name to indicate it's an API test
        test_data["name"] = f"API Test - {test_data['name']}"
    
    response = requests.post(f"{API_BASE}/generate-resume", json=test_data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"Status: {response.status_code}")
        print(f"Message: {result['message']}")
        print(f"Generated file: {result['filename']}")
        print(f"Download URL: {result['download_url']}")
        
        # Test downloading the file
        download_response = requests.get(f"{API_BASE}{result['download_url']}")
        if download_response.status_code == 200:
            # Save the PDF locally
            with open(f"test_resume.pdf", "wb") as f:
                f.write(download_response.content)
            print(f"PDF downloaded successfully as: test_resume.pdf")
        else:
            print(f"Failed to download PDF: {download_response.status_code}")
    else:
        print(f"Failed to generate resume: {response.status_code}")
        print(f"Error: {response.text}")
    
    print("-" * 50)

def test_upload_yaml():
    """Test uploading YAML file"""
    print("Testing YAML file upload...")
    
    try:
        with open('resume.yaml', 'rb') as f:
            files = {'file': ('resume.yaml', f, 'application/x-yaml')}
            response = requests.post(f"{API_BASE}/upload-yaml", files=files)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Status: {response.status_code}")
            print(f"Message: {result['message']}")
            print(f"Generated file: {result['filename']}")
            print(f"Download URL: {result['download_url']}")
            
            # Test downloading the file
            download_response = requests.get(f"{API_BASE}{result['download_url']}")
            if download_response.status_code == 200:
                with open(f"uploaded_resume.pdf", "wb") as f:
                    f.write(download_response.content)
                print(f"PDF downloaded successfully as: uploaded_resume.pdf")
            else:
                print(f"Failed to download PDF: {download_response.status_code}")
        else:
            print(f"Failed to upload YAML: {response.status_code}")
            print(f"Error: {response.text}")
            
    except FileNotFoundError:
        print("resume.yaml file not found. Skipping YAML upload test.")
    
    print("-" * 50)

def test_get_template():
    """Test getting the LaTeX template"""
    print("Testing template retrieval...")
    response = requests.get(f"{API_BASE}/template")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Status: {response.status_code}")
        print(f"Template length: {len(result['template'])} characters")
        print("Template retrieved successfully")
    else:
        print(f"Failed to get template: {response.status_code}")
        print(f"Error: {response.text}")
    
    print("-" * 50)

def main():
    """Run all tests"""
    print("Starting FastAPI Resume Builder Tests")
    print("=" * 50)
    
    try:
        # Test basic endpoints
        test_health_check()
        
        # Get sample data for testing
        sample_data = test_sample_data()
        
        # Test resume generation
        test_generate_resume_json(sample_data)
        
        # Test YAML upload
        test_upload_yaml()
        
        # Test template retrieval
        test_get_template()
        
        print("All tests completed!")
        print("\nTo clean up temporary files, you can call:")
        print(f"curl -X DELETE {API_BASE}/cleanup")
        
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to {API_BASE}")
        print("Make sure the FastAPI server is running:")
        print("  python3 main.py")
        print("  or")
        print("  uvicorn main:app --reload")

if __name__ == "__main__":
    main() 