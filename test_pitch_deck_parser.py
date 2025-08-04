#!/usr/bin/env python3
"""
Test script to verify pitch deck parser functionality.
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_pitch_deck_parser():
    """Test the pitch deck parser functionality"""
    print("🚀 Starting Pitch Deck Parser Tests...")
    
    try:
        from agents.pitchdeck_parser import extract_slide_data, get_pitch_deck_summary, parse_pitch_deck
        from agents.company_researcher import CompanyResearcher
        from agents.memo_generator import generate_memo
        from models.schemas import StructuredCompanyDoc
        
        print("🧪 Testing Pitch Deck Parser...")
        
        # Test with sample PDF
        pdf_path = "data/sample_pitch_deck.pdf"
        
        if os.path.exists(pdf_path):
            print(f"📄 Found test PDF: {pdf_path}")
            
            # Test slide data extraction
            print("\n🔍 Testing slide data extraction...")
            slides = extract_slide_data(pdf_path)
            print(f"   ✅ Extracted {len(slides)} slides")
            
            if slides:
                print("   📊 Sample slide content:")
                for slide in slides[:2]:  # Show first 2 slides
                    print(f"      • Slide {slide['slide_number']}")
                    print(f"      • Text length: {len(slide['text'])} chars")
                    print(f"      • Has OCR: {'Yes' if slide.get('image_content') else 'No'}")
            
            # Test pitch deck summary
            print("\n📋 Testing pitch deck summary...")
            summary = get_pitch_deck_summary(pdf_path)
            print(f"   ✅ Summary generated")
            print(f"      • Total slides: {summary.get('total_slides', 'Unknown')}")
            print(f"      • Content patterns: {summary.get('content_patterns', [])}")
            print(f"      • Has images: {summary.get('has_images', False)}")
            
            # Test full parsing
            print("\n🤖 Testing full pitch deck parsing...")
            sections = parse_pitch_deck(pdf_path)
            print(f"   ✅ Parsed {len(sections)} sections")
            
            # Test integration with company researcher
            print("\n🔗 Testing integration with company researcher...")
            researcher = CompanyResearcher()
            company_doc = researcher.analyze_pitch_deck(pdf_path, "Test Company")
            
            print(f"   ✅ Company document created")
            print(f"      • Company name: {company_doc.name}")
            print(f"      • Populated sections: {len(company_doc.get_populated_sections())}")
            
            # Test memo generation
            memo = generate_memo(company_doc)
            print(f"      • Memo generated: {len(memo)} characters")
            
        else:
            print(f"⚠️ Test PDF not found: {pdf_path}")
            print("   Create a sample pitch deck PDF to test the parser")
            
            # Test with mock data
            print("\n🧪 Testing with mock data...")
            mock_sections = {
                "problem": {
                    "text": "Traditional design tools are too complex for non-designers",
                    "bullets": ["High learning curve", "Expensive software", "Limited collaboration"],
                    "citations": ["https://pitch_deck_slide_2.pdf"]
                },
                "solution": {
                    "text": "AI-powered design platform for everyone",
                    "bullets": ["Drag-and-drop interface", "AI design suggestions", "Real-time collaboration"],
                    "citations": ["https://pitch_deck_slide_3.pdf"]
                }
            }
            
            print(f"   ✅ Mock sections created: {len(mock_sections)} sections")
            for section_name, section_data in mock_sections.items():
                print(f"      • {section_name}: {len(section_data['text'])} chars")
        
        # Test integration with memo generation
        print("\n🔗 Testing Pitch Deck Integration...")
        
        # Create mock pitch deck sections
        from models.schemas import Section, Citation
        from datetime import datetime
        
        mock_sections = {
            "problem": Section(
                text="Traditional design tools are too complex for non-designers",
                bullets=["High learning curve", "Expensive software", "Limited collaboration"],
                citations=[Citation(
                    url="https://pitch_deck_slide_2.pdf",
                    snippet="Pitch deck content",
                    source_type="pitch_deck",
                    timestamp=datetime.now()
                )]
            ),
            "solution": Section(
                text="AI-powered design platform for everyone",
                bullets=["Drag-and-drop interface", "AI design suggestions", "Real-time collaboration"],
                citations=[Citation(
                    url="https://pitch_deck_slide_3.pdf",
                    snippet="Pitch deck content",
                    source_type="pitch_deck",
                    timestamp=datetime.now()
                )]
            ),
            "team": Section(
                text="Experienced team with backgrounds in design and technology",
                bullets=["CEO: Former design lead at major tech company", "CTO: 10+ years in software development"],
                citations=[Citation(
                    url="https://pitch_deck_slide_8.pdf",
                    snippet="Pitch deck content",
                    source_type="pitch_deck",
                    timestamp=datetime.now()
                )]
            )
        }
        
        print(f"   ✅ Created mock pitch deck sections: {len(mock_sections)} sections")
        
        # Create company document from pitch deck data
        company_doc = StructuredCompanyDoc(name="DesignTech")
        
        # Apply pitch deck sections to company document
        for section_name, section_obj in mock_sections.items():
            if hasattr(company_doc, section_name):
                setattr(company_doc, section_name, section_obj)
        
        # Generate memo
        memo = generate_memo(company_doc)
        
        print(f"   ✅ Generated memo from pitch deck data: {len(memo)} characters")
        print(f"   📄 Sample memo content:")
        print(f"      {memo[:100]}...")
        
        print("\n🎉 Pitch deck parser tests completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_pitch_deck_parser() 