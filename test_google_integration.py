#!/usr/bin/env python3
"""
Test script to demonstrate the Google search integration
Note: Requires SERPAPI_KEY environment variable
"""

import os
from agents.company_researcher import CompanyResearcher

def test_google_integration():
    """Test the Google search integration"""
    
    # Check if API key is available
    if not os.getenv('SERPAPI_KEY'):
        print("⚠️  SERPAPI_KEY not found in environment variables")
        print("   To test Google search integration, set your SerpAPI key:")
        print("   export SERPAPI_KEY='your_api_key_here'")
        print("\n   For now, testing with website-only analysis...")
        
        # Test with website-only analysis
        test_company = {"name": "Linear", "website": "https://linear.app"}
        
        researcher = CompanyResearcher()
        try:
            company_doc = researcher.analyze_company(test_company['name'], test_company['website'])
            
            print(f"\n✅ Website-only analysis for {test_company['name']}:")
            populated = company_doc.get_populated_sections()
            print(f"   Found {len(populated)} populated sections")
            
            for section_name, section in populated.items():
                if section.text:
                    print(f"   • {section_name}: {section.text[:100]}...")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        return
    
    # Test with Google search integration
    test_companies = [
        {"name": "Linear", "website": "https://linear.app"},
        {"name": "Figma", "website": "https://figma.com"}
    ]
    
    researcher = CompanyResearcher()
    
    for company in test_companies:
        print(f"\n{'='*60}")
        print(f"Testing Google integration: {company['name']}")
        print(f"{'='*60}")
        
        try:
            # Analyze company with Google search
            company_doc = researcher.analyze_company(company['name'], company['website'])
            
            # Show populated sections
            populated = company_doc.get_populated_sections()
            print(f"\n✅ Found {len(populated)} populated sections:")
            for section_name, section in populated.items():
                if section.text:
                    print(f"  • {section_name}: {section.text[:100]}...")
                elif section.bullets:
                    print(f"  • {section_name}: {len(section.bullets)} bullets")
                elif section.metrics:
                    print(f"  • {section_name}: {len(section.metrics)} metrics")
            
            # Show missing sections
            missing = company_doc.get_missing_fields()
            print(f"\n❌ Missing {len(missing)} sections: {', '.join(missing)}")
            
            # Show citations by source type
            all_citations = []
            for section in populated.values():
                all_citations.extend(section.citations)
            
            source_types = {}
            for citation in all_citations:
                source_types[citation.source_type] = source_types.get(citation.source_type, 0) + 1
            
            print(f"\n📊 Citations by source:")
            for source_type, count in source_types.items():
                print(f"  • {source_type}: {count} citations")
            
        except Exception as e:
            print(f"❌ Error analyzing {company['name']}: {e}")

if __name__ == "__main__":
    test_google_integration() 