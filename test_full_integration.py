#!/usr/bin/env python3
"""
Test script to verify full system integration.
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_full_integration():
    """Test the full system integration"""
    print("🚀 Starting Full System Integration Tests...")
    
    try:
        from agents.company_researcher import CompanyResearcher
        from agents.memo_generator import generate_memo
        from models.schemas import StructuredCompanyDoc, Section
        from utils.pdf_generator import generate_pdf_with_charts
        from agents.founder_profiler import get_founder_team_info
        from utils.chart_generator import generate_charts_for_memo
        
        # Test companies
        test_companies = [
            {"name": "Canva", "website": "https://www.canva.com"},
            {"name": "Figma", "website": "https://www.figma.com"},
            {"name": "Notion", "website": "https://www.notion.so"}
        ]
        
        for company in test_companies:
            print(f"\n🧪 Testing {company['name']}...")
            
            try:
                # Test company research
                researcher = CompanyResearcher()
                company_doc = researcher.analyze_company(
                    company['name'], 
                    company['website']
                )
                
                print(f"   ✅ Company research completed")
                print(f"      • Company: {company_doc.name}")
                print(f"      • Populated sections: {len(company_doc.get_populated_sections())}")
                
                # Test memo generation
                memo = generate_memo(company_doc)
                print(f"   ✅ Memo generated: {len(memo)} characters")
                
                # Test PDF generation
                try:
                    pdf_path = f"data/memos/{company['name'].replace(' ', '_')}_test_memo.pdf"
                    generate_pdf_with_charts(memo, pdf_path, company_doc, company['name'])
                    print(f"   ✅ PDF generated: {pdf_path}")
                except Exception as e:
                    print(f"   ⚠️ PDF generation failed: {e}")
                
                # Test chart generation
                try:
                    chart_paths = generate_charts_for_memo(company['name'], company_doc)
                    if chart_paths:
                        print(f"   ✅ Charts generated: {len(chart_paths)} charts")
                    else:
                        print(f"   ⚠️ No charts generated (insufficient data)")
                except Exception as e:
                    print(f"   ⚠️ Chart generation failed: {e}")
                
                # Test dynamic team info
                try:
                    team_section = get_founder_team_info(company['name'])
                    if team_section.has_content():
                        print(f"   ✅ Team info retrieved: {len(team_section.text)} chars")
                    else:
                        print(f"   ⚠️ No team info available")
                except Exception as e:
                    print(f"   ⚠️ Team info failed: {e}")
                
            except Exception as e:
                print(f"   ❌ Failed to analyze {company['name']}: {e}")
        
        print("\n🎉 Full integration tests completed!")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

if __name__ == "__main__":
    test_full_integration() 