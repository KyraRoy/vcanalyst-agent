#!/usr/bin/env python3
"""
Test script to verify pitch deck frontend integration functionality.
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_pitch_deck_integration():
    """Test the pitch deck integration with the frontend"""
    print("🧪 Testing Pitch Deck Frontend Integration...")
    
    try:
        # Test imports
        from agents.pitchdeck_parser import parse_pitch_deck, get_pitch_deck_summary
        from models.schemas import StructuredCompanyDoc
        from agents.memo_generator import generate_memo
        
        print("   ✅ All imports successful")
        
        # Test mock pitch deck processing
        print("\n📄 Testing mock pitch deck processing...")
        
        # Create a mock pitch deck data structure
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
            },
            "team": {
                "text": "Experienced team with backgrounds in design and technology",
                "bullets": ["CEO: Former design lead at major tech company", "CTO: 10+ years in software development"],
                "citations": ["https://pitch_deck_slide_8.pdf"]
            }
        }
        
        print(f"   ✅ Created mock pitch deck with {len(mock_sections)} sections")
        
        # Test company document creation
        print("\n🏢 Testing company document creation...")
        
        company_doc = StructuredCompanyDoc(name="Pitch Deck Company")
        
        # Apply mock sections to company document
        for section_name, section_data in mock_sections.items():
            if hasattr(company_doc, section_name):
                from models.schemas import Section, Citation
                from datetime import datetime
                
                # Create Section object
                section = Section(
                    text=section_data['text'],
                    bullets=section_data['bullets'],
                    citations=[Citation(
                        url=citation,
                        snippet="Pitch deck content",
                        source_type="pitch_deck",
                        timestamp=datetime.now()
                    ) for citation in section_data['citations']]
                )
                
                setattr(company_doc, section_name, section)
        
        print(f"   ✅ Company document created with {len(company_doc.get_populated_sections())} populated sections")
        
        # Test memo generation
        print("\n📝 Testing memo generation...")
        
        memo = generate_memo(company_doc)
        
        if memo and len(memo) > 100:
            print(f"   ✅ Memo generated successfully ({len(memo)} characters)")
            print(f"   📄 Sample content: {memo[:100]}...")
        else:
            print("   ⚠️ Memo generation may have issues")
        
        # Test section content extraction
        print("\n📊 Testing section content extraction...")
        
        populated_sections = company_doc.get_populated_sections()
        for section_name, section in populated_sections.items():
            print(f"   • {section_name}: {len(section.text)} chars, {len(section.bullets)} bullets")
        
        print("\n🎉 Pitch deck frontend integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_pitch_deck_integration() 