#!/usr/bin/env python3
"""
Test script to verify enhanced GPT-4 analysis functionality.
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_enhanced_analysis():
    """Test the enhanced GPT-4 analysis"""
    print("🧪 Testing Enhanced GPT-4 Analysis...")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    try:
        # Check if OpenAI API key is available
        if not os.getenv("OPENAI_API_KEY"):
            print("   ⚠️ OPENAI_API_KEY not found - enhanced analysis will not work")
            print("   📝 Run 'python3 setup_api_keys.py' to configure API keys")
            return False
        
        from agents.enhanced_analyzer import EnhancedAnalyzer
        
        print("   ✅ EnhancedAnalyzer imported successfully")
        
        # Test with sample pitch deck data
        sample_slides = [
            {
                "slide_number": 1,
                "text": """
                DesignTech
                AI-Powered Design Platform
                
                The Problem
                • Traditional design tools are too complex for non-designers
                • High learning curve and expensive software
                • Limited collaboration features
                """
            },
            {
                "slide_number": 2,
                "text": """
                Our Solution
                • AI-powered design platform for everyone
                • Drag-and-drop interface with smart suggestions
                • Real-time collaboration and sharing
                • Affordable pricing model
                """
            },
            {
                "slide_number": 3,
                "text": """
                Market Opportunity
                • $50 billion design software market
                • Growing at 15% annually
                • 100M+ potential users worldwide
                • TAM: $200 billion including adjacent markets
                """
            },
            {
                "slide_number": 4,
                "text": """
                Traction
                • 100,000+ active users
                • $2M ARR growing 300% YoY
                • 50,000+ designs created
                • 95% customer satisfaction rate
                """
            },
            {
                "slide_number": 5,
                "text": """
                Team
                • CEO: Former design lead at major tech company
                • CTO: 10+ years in software development
                • CPO: UX expert with successful exits
                • Founded in 2022, based in San Francisco
                """
            }
        ]
        
        print("   📊 Testing GPT-4 analysis with sample data...")
        
        analyzer = EnhancedAnalyzer()
        sections = analyzer.analyze_pitch_deck_with_gpt(sample_slides, "DesignTech")
        
        if sections:
            print(f"   ✅ GPT-4 analysis successful! Found {len(sections)} sections:")
            for section_name, section in sections.items():
                print(f"      • {section_name}: {len(section.text)} chars, {len(section.bullets)} bullets")
        else:
            print("   ❌ GPT-4 analysis failed")
            return False
        
        # Test web research enhancement
        print("\n   🔍 Testing web research enhancement...")
        
        research_sections = analyzer.enhance_with_web_research("DesignTech", "design software")
        
        if research_sections:
            print(f"   ✅ Web research successful! Found {len(research_sections)} additional sections")
        else:
            print("   ⚠️ Web research returned no results (this is normal without SERPAPI)")
        
        # Test comprehensive memo creation
        print("\n   📝 Testing comprehensive memo creation...")
        
        company_doc = analyzer.create_comprehensive_memo(sections, research_sections, "DesignTech")
        
        if company_doc:
            populated_sections = company_doc.get_populated_sections()
            print(f"   ✅ Comprehensive memo created with {len(populated_sections)} populated sections")
            
            # Test memo generation
            from agents.memo_generator import generate_memo
            memo = generate_memo(company_doc)
            
            if memo and len(memo) > 500:
                print(f"   ✅ Memo generated successfully ({len(memo)} characters)")
                print(f"   📄 Sample: {memo[:200]}...")
            else:
                print("   ⚠️ Memo generation may have issues")
        else:
            print("   ❌ Comprehensive memo creation failed")
            return False
        
        print("\n🎉 Enhanced analysis test completed successfully!")
        return True
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_enhanced_analysis() 