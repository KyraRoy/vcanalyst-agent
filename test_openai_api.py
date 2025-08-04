#!/usr/bin/env python3
"""
Test script to verify OpenAI API key is working.
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

def test_openai_api():
    """Test if OpenAI API key is working"""
    print("🧪 Testing OpenAI API...")
    
    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment variables")
        return False
    
    print(f"✅ API key found: {api_key[:20]}...")
    
    try:
        # Create OpenAI client
        client = OpenAI(api_key=api_key)
        
        # Test with a simple request
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {
                    "role": "user",
                    "content": "Say 'Hello, API is working!'"
                }
            ],
            max_tokens=50
        )
        
        content = response.choices[0].message.content.strip()
        print(f"✅ API test successful! Response: {content}")
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

if __name__ == "__main__":
    test_openai_api() 