#!/usr/bin/env python3
"""
Test script to demonstrate the improved text extraction pipeline
"""

import json
from agents.company_researcher import CompanyResearcher
from models.schemas import StructuredCompanyDoc

def test_extraction():
    """Test the extraction pipeline with a sample company"""
    
    # Test with a smaller company that might have more detailed info
    test_companies = [
        {"name": "Linear", "website": "https://linear.app"},
        {"name": "Figma", "website": "https://figma.com"},
        {"name": "Airtable", "website": "https://airtable.com"}
    ]
    
    researcher = CompanyResearcher()
    
    for company in test_companies:
        print(f"\n{'='*60}")
        print(f"Testing: {company['name']}")
        print(f"{'='*60}")
        
        try:
            # Analyze company
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
            
            # Show sample of cleaned text
            if company_doc.intro.text:
                print(f"\n📝 Sample cleaned text:")
                print(f"  {company_doc.intro.text[:200]}...")
            
        except Exception as e:
            print(f"❌ Error analyzing {company['name']}: {e}")

if __name__ == "__main__":
    test_extraction() 