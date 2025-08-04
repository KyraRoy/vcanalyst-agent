#!/usr/bin/env python3
"""
Test script to show extracted content from pitch deck without GPT-4.
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_pitch_deck_content():
    """Test the pitch deck content extraction"""
    print("🧪 Testing Pitch Deck Content Extraction...")
    
    try:
        from agents.pitchdeck_parser import extract_slide_data
        
        # Test with our sample PDF
        pdf_path = "data/sample_pitch_deck.pdf"
        
        if not os.path.exists(pdf_path):
            print(f"❌ Test PDF not found: {pdf_path}")
            return
        
        print(f"📄 Testing with: {pdf_path}")
        
        # Extract slide data
        slides = extract_slide_data(pdf_path)
        
        print(f"✅ Extracted {len(slides)} slides")
        
        # Show content from each slide
        for i, slide in enumerate(slides):
            print(f"\n📊 Slide {slide['slide_number']}:")
            print(f"   Text length: {len(slide['text'])} chars")
            print(f"   Raw text length: {len(slide['raw_text'])} chars")
            print(f"   Image content length: {len(slide['image_content'])} chars")
            
            # Show first 200 chars of text
            preview = slide['text'][:200] + "..." if len(slide['text']) > 200 else slide['text']
            print(f"   Preview: {preview}")
        
        # Test the structured content format
        print(f"\n🔍 Testing structured content format...")
        for slide in slides:
            print(f"\n📄 Slide {slide['slide_number']} structured content:")
            print("=" * 50)
            print(slide['text'])
            print("=" * 50)
        
        print(f"\n🎉 Content extraction test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_pitch_deck_content() 