#!/usr/bin/env python3
"""
Test script to demonstrate the LinkedIn team extraction integration via founder profiler
Note: Requires SERPAPI_KEY environment variable
"""

import os
from agents.company_researcher import CompanyResearcher
from agents.founder_profiler import evaluate_founder

def test_linkedin_integration():
    """Test the LinkedIn team extraction integration via founder profiler"""
    
    # Check if API key is available
    if not os.getenv('SERPAPI_KEY'):
        print("⚠️  SERPAPI_KEY not found in environment variables")
        print("   To test LinkedIn integration, set your SerpAPI key:")
        print("   export SERPAPI_KEY='your_api_key_here'")
        print("\n   For now, testing with mock data...")
        
        # Test with mock LinkedIn data
        test_company = {"name": "Linear", "website": "https://linear.app", "founder": "Karri Saarinen"}
        
        researcher = CompanyResearcher()
        try:
            company_doc = researcher.analyze_company(
                test_company['name'], 
                test_company['website'], 
                test_company['founder']
            )
            
            print(f"\n✅ Analysis for {test_company['name']}:")
            populated = company_doc.get_populated_sections()
            print(f"   Found {len(populated)} populated sections")
            
            for section_name, section in populated.items():
                if section.text:
                    print(f"   • {section_name}: {section.text[:100]}...")
                elif section.bullets:
                    print(f"   • {section_name}: {len(section.bullets)} bullets")
                    if section_name == 'team' and section.bullets:
                        print(f"     Team members:")
                        for bullet in section.bullets[:3]:  # Show first 3
                            print(f"       - {bullet}")
                elif section.metrics:
                    print(f"   • {section_name}: {len(section.metrics)} metrics")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        return
    
    # Test with real LinkedIn integration
    test_companies = [
        {"name": "Linear", "website": "https://linear.app", "founder": "Karri Saarinen"},
        {"name": "Figma", "website": "https://figma.com", "founder": "Dylan Field"},
        {"name": "Notion", "website": "https://notion.so", "founder": "Ivan Zhao"}
    ]
    
    researcher = CompanyResearcher()
    
    for company in test_companies:
        print(f"\n{'='*60}")
        print(f"Testing LinkedIn integration: {company['name']}")
        print(f"{'='*60}")
        
        try:
            # Test founder profiler separately first
            print(f"\n🔍 Testing founder profiler with LinkedIn...")
            founder_data = evaluate_founder(company['founder'], company['name'])
            
            if founder_data.get('team') and founder_data['team'].bullets:
                print(f"✅ Found {len(founder_data['team'].bullets)} team members:")
                for bullet in founder_data['team'].bullets[:3]:  # Show first 3
                    print(f"   • {bullet}")
            else:
                print("❌ No team members found")
            
            # Now test full integration
            print(f"\n🔍 Testing full company analysis...")
            company_doc = researcher.analyze_company(
                company['name'], 
                company['website'], 
                company['founder']
            )
            
            # Show populated sections
            populated = company_doc.get_populated_sections()
            print(f"\n✅ Found {len(populated)} populated sections:")
            for section_name, section in populated.items():
                if section.text:
                    print(f"  • {section_name}: {section.text[:100]}...")
                elif section.bullets:
                    print(f"  • {section_name}: {len(section.bullets)} bullets")
                    if section_name == 'team' and section.bullets:
                        print(f"    Team members:")
                        for bullet in section.bullets[:3]:  # Show first 3
                            print(f"      - {bullet}")
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
    test_linkedin_integration() 