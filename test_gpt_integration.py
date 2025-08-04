#!/usr/bin/env python3
"""
Test script to verify GPT-4 integration with section extraction.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm.section_extractor import extract_sections_with_gpt
from models.schemas import RawDoc
from datetime import datetime

def test_gpt_integration():
    """Test GPT-4 section extraction"""
    print("🧪 Testing GPT-4 Integration...")
    
    # Check if OpenAI API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️ OPENAI_API_KEY not found in environment variables")
        print("   Please set your OpenAI API key to test GPT-4 extraction")
        return False
    
    try:
        # Create test documents
        test_docs = [
            RawDoc(
                url="https://example.com/about",
                title="About Canva",
                text="Canva is an online design platform that makes it easy to create professional designs. Founded in 2013, Canva has over 100 million users worldwide. The company aims to democratize design by making it accessible to everyone, not just professionals.",
                source_type="website",
                timestamp=datetime.now()
            ),
            RawDoc(
                url="https://example.com/pricing",
                title="Canva Pricing",
                text="Canva offers a freemium model with a free tier and premium Pro plan at $12.99/month. The platform generates revenue through subscriptions and enterprise sales. Canva has raised over $200 million in funding.",
                source_type="website",
                timestamp=datetime.now()
            )
        ]
        
        print("✅ Successfully created test documents")
        
        # Test GPT-4 extraction
        print("🔍 Testing GPT-4 extraction for 'Canva'...")
        sections = extract_sections_with_gpt("Canva", test_docs)
        
        if sections:
            print("✅ GPT-4 extraction successful!")
            print(f"📊 Found {len(sections)} populated sections:")
            
            for section_name, section in sections.items():
                if section.has_content():
                    print(f"   • {section_name}: {len(section.bullets)} bullets, {len(section.citations)} citations")
        else:
            print("⚠️ GPT-4 extraction returned no results")
            return False
        
        print("\n🎉 GPT-4 integration test passed!")
        return True
        
    except Exception as e:
        print(f"❌ GPT-4 integration test failed: {e}")
        return False

if __name__ == "__main__":
    test_gpt_integration() 