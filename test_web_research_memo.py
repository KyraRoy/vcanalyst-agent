#!/usr/bin/env python3
"""
Test script to verify web research memo generation functionality.
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_web_research_memo():
    """Test web research memo generation"""
    print("🧪 Testing Web Research Memo Generation...")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    try:
        # Check if OpenAI API key is available
        if not os.getenv("OPENAI_API_KEY"):
            print("   ⚠️ OPENAI_API_KEY not found - web research will not work")
            print("   📝 Run 'python3 setup_api_keys.py' to configure API keys")
            return False
        
        from agents.enhanced_analyzer import EnhancedAnalyzer
        
        print("   ✅ EnhancedAnalyzer imported successfully")
        
        # Test with a well-known company
        test_company = "Stripe"
        test_industry = "fintech"
        
        print(f"   📊 Testing web research memo generation for {test_company}...")
        
        analyzer = EnhancedAnalyzer()
        company_doc = analyzer.generate_memo_from_web_research(test_company, test_industry)
        
        if company_doc:
            populated_sections = company_doc.get_populated_sections()
            print(f"   ✅ Web research successful! Found {len(populated_sections)} populated sections:")
            
            for section_name, section in populated_sections.items():
                print(f"      • {section_name}: {len(section.text)} chars, {len(section.bullets)} bullets")
            
            # Test memo generation
            from agents.memo_generator import generate_memo
            memo = generate_memo(company_doc)
            
            if memo and len(memo) > 1000:
                print(f"   ✅ Memo generated successfully ({len(memo)} characters)")
                print(f"   📄 Sample content: {memo[:300]}...")
            else:
                print("   ⚠️ Memo generation may have issues")
        else:
            print("   ❌ Web research memo generation failed")
            return False
        
        print("\n🎉 Web research memo generation test completed successfully!")
        return True
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_web_research_memo() 