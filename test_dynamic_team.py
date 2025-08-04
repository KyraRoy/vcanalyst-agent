#!/usr/bin/env python3
"""
Test script to verify dynamic team information functionality.
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_dynamic_team():
    """Test the dynamic team information functionality"""
    print("🧪 Testing Dynamic Team Information...")
    
    try:
        from agents.founder_profiler import get_founder_team_info
        
        # Test companies
        test_companies = ["Canva", "Figma", "Notion", "Stripe", "Airbnb"]
        
        for company_name in test_companies:
            print(f"\n📊 Testing {company_name}...")
            
            try:
                team_section = get_founder_team_info(company_name)
                
                if team_section.has_content():
                    print(f"   ✅ Team info retrieved")
                    print(f"      • Text length: {len(team_section.text)} chars")
                    print(f"      • Bullets: {len(team_section.bullets)}")
                    print(f"      • Citations: {len(team_section.citations)}")
                    
                    # Show sample content
                    if team_section.text:
                        preview = team_section.text[:100] + "..." if len(team_section.text) > 100 else team_section.text
                        print(f"      • Preview: {preview}")
                else:
                    print(f"   ⚠️ No team info available")
                    
            except Exception as e:
                print(f"   ❌ Failed to get team info: {e}")
        
        print("\n🎉 Dynamic team tests completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_dynamic_team() 