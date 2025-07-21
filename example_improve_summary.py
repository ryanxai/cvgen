#!/usr/bin/env python3

"""
Example script demonstrating how to use the improve-summary endpoint
"""

import requests
import json

def demonstrate_improve_summary():
    """Demonstrate the improve-summary endpoint with different examples"""
    
    # API endpoint
    base_url = "http://localhost:8000"
    
    # Example 1: Professional summary improvement
    example1 = {
        "instructions": "You are a professional recruiter. Improve the writing style of the following summary section to be more professional and concise. Focus on action verbs and quantifiable achievements. Don't provide any other text than the improved summary section.",
        "summary": "Senior Data Scientist and ML Engineer with 10+ years of expertise in NLP, speech processing, and generative AI. Demonstrated success developing LLM-based systems achieving high accuracy metrics. Specialized in building end-to-end AI solutions from concept to production, combining deep learning architectures with practical business applications for start-ups and big companies."
    }
    
    # Example 2: Entry-level summary improvement
    example2 = {
        "instructions": "You are a professional recruiter. Improve the writing style of the following summary section to be more professional and impactful for an entry-level position. Focus on transferable skills and potential. Don't provide any other text than the improved summary section.",
        "summary": "Recent graduate with a degree in Computer Science. I like programming and have done some projects. I know Python and JavaScript. I'm looking for a job where I can learn and grow."
    }
    
    # Example 3: Career transition summary
    example3 = {
        "instructions": "You are a professional recruiter. Improve the writing style of the following summary section for someone transitioning from marketing to data science. Emphasize transferable skills and relevant experience. Don't provide any other text than the improved summary section.",
        "summary": "Marketing professional with 5 years of experience in digital marketing and analytics. I've worked with data analysis tools and have a strong understanding of customer behavior. I'm currently learning Python and machine learning to transition into a data science role."
    }
    
    examples = [
        ("Professional Summary Improvement", example1),
        ("Entry-Level Summary Improvement", example2),
        ("Career Transition Summary", example3)
    ]
    
    print("🚀 Resume Summary Improvement Examples")
    print("=" * 60)
    
    for title, data in examples:
        print(f"\n📝 {title}")
        print("-" * 40)
        print(f"Original Summary:\n{data['summary']}")
        print(f"\nInstructions:\n{data['instructions']}")
        
        try:
            response = requests.post(
                f"{base_url}/improve-summary",
                json=data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n✅ Improved Summary:\n{result['improved_summary']}")
            else:
                print(f"\n❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("\n❌ Connection Error: Make sure the API server is running on http://localhost:8000")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    demonstrate_improve_summary() 