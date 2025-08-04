#!/usr/bin/env python3
"""
Test script to debug pitch deck extraction.
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_pitch_deck_extraction():
    """Test pitch deck extraction with debugging"""
    print("🧪 Testing Pitch Deck Extraction...")
    
    try:
        from agents.pitchdeck_parser import extract_slide_data, analyze_slide_with_rules
        
        # Test with a sample PDF if available
        test_pdf_path = "data/sample_pitch_deck.pdf"
        
        if not os.path.exists(test_pdf_path):
            print(f"   ⚠️ Test PDF not found at {test_pdf_path}")
            print("   📝 Creating a simple test...")
            
            # Test the rule-based analysis with sample text
            sample_text = """
            Problem: Traditional design tools are too complex for non-designers.
            Users struggle with steep learning curves and expensive software.
            
            Solution: Our AI-powered design platform makes professional design accessible to everyone.
            Features include drag-and-drop interface and real-time collaboration.
            
            Team: Founded by experienced designers and engineers from major tech companies.
            CEO has 10+ years in design industry.
            
            Market: $50 billion design software market growing at 15% annually.
            TAM of $200 billion including adjacent markets.
            
            Traction: 100,000+ active users, $2M ARR, 300% year-over-year growth.
            Raised $5M Series A in 2023.
            """
            
            print("   📊 Testing rule-based analysis with sample text...")
            result = analyze_slide_with_rules(1, sample_text)
            
            if result:
                print(f"   ✅ Rule-based analysis successful! Found {len(result)} sections:")
                for section_name, section_data in result.items():
                    print(f"      • {section_name}: {len(section_data.get('text', ''))} chars")
            else:
                print("   ❌ Rule-based analysis failed")
            
            return True
        
        print(f"   📄 Testing with PDF: {test_pdf_path}")
        
        # Extract slide data
        slides = extract_slide_data(test_pdf_path)
        
        if slides:
            print(f"   ✅ Extracted {len(slides)} slides")
            
            # Test rule-based analysis on first slide
            if slides:
                first_slide = slides[0]
                print(f"   📊 Testing rule-based analysis on slide {first_slide['slide_number']}")
                print(f"   📝 Slide text length: {len(first_slide['text'])} characters")
                
                if len(first_slide['text']) > 50:
                    print(f"   📄 Sample text: {first_slide['text'][:200]}...")
                    
                    result = analyze_slide_with_rules(
                        first_slide['slide_number'],
                        first_slide['text']
                    )
                    
                    if result:
                        print(f"   ✅ Rule-based analysis successful! Found {len(result)} sections:")
                        for section_name, section_data in result.items():
                            print(f"      • {section_name}: {len(section_data.get('text', ''))} chars")
                    else:
                        print("   ❌ Rule-based analysis found no sections")
                else:
                    print("   ⚠️ Slide text too short for meaningful analysis")
            else:
                print("   ❌ No slides extracted")
        else:
            print("   ❌ Failed to extract slides from PDF")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_pitch_deck_extraction() 