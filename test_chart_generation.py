#!/usr/bin/env python3
"""
Test script to verify chart generation functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.chart_generator import generate_charts, extract_market_numbers, extract_funding_data, extract_traction_data
from models.schemas import StructuredCompanyDoc, Section
from datetime import datetime

def test_chart_generation():
    """Test chart generation with sample data"""
    print("🧪 Testing Chart Generation...")
    
    # Create sample structured document with chart-worthy data
    test_doc = StructuredCompanyDoc(name="Test Company")
    
    # Market data
    test_doc.market = Section(
        text="The total addressable market (TAM) is estimated at $50 billion, with a serviceable addressable market (SAM) of $10 billion and a serviceable obtainable market (SOM) of $2 billion.",
        bullets=["TAM: $50B", "SAM: $10B", "SOM: $2B"],
        citations=[]
    )
    
    # Funding data
    test_doc.funding = Section(
        text="The company has raised multiple funding rounds.",
        bullets=[
            "2020: $5M Seed round led by Y Combinator",
            "2021: $25M Series A led by a16z",
            "2022: $100M Series B led by Sequoia",
            "2023: $200M Series C led by Tiger Global"
        ],
        citations=[]
    )
    
    # Traction data
    test_doc.traction = Section(
        text="Strong user growth over the past three years.",
        bullets=[
            "1M users in 2021",
            "5M users in 2022", 
            "10M users in 2023",
            "Revenue: $10M in 2022, $25M in 2023"
        ],
        metrics={
            "Users": "10M in 2023",
            "Revenue": "$25M in 2023",
            "Growth": "100% YoY"
        },
        citations=[]
    )
    
    print("✅ Successfully created test document with chart data")
    
    # Test market number extraction
    print("🔍 Testing market number extraction...")
    market_text = test_doc.market.text + " " + " ".join(test_doc.market.bullets)
    market_data = extract_market_numbers(market_text)
    print(f"   Extracted market data: {market_data}")
    
    # Test funding data extraction
    print("🔍 Testing funding data extraction...")
    funding_data = extract_funding_data(test_doc.funding.bullets)
    print(f"   Extracted {len(funding_data)} funding rounds")
    for round_data in funding_data:
        print(f"   - {round_data['year']}: ${round_data['amount']:.0f}M {round_data['round']}")
    
    # Test traction data extraction
    print("🔍 Testing traction data extraction...")
    traction_data = extract_traction_data(test_doc.traction.metrics, test_doc.traction.bullets)
    print(f"   Extracted {len(traction_data)} traction data points")
    for traction_point in traction_data:
        print(f"   - {traction_point['year']}: {traction_point['value']:.0f}M {traction_point['metric']}")
    
    # Test chart generation
    print("🔍 Testing chart generation...")
    output_dir = "test_charts"
    chart_paths = generate_charts(test_doc, output_dir)
    
    if chart_paths:
        print("✅ Chart generation successful!")
        print(f"📊 Generated {len(chart_paths)} charts:")
        for chart_type, chart_path in chart_paths.items():
            if os.path.exists(chart_path):
                print(f"   • {chart_type}: {chart_path}")
            else:
                print(f"   • {chart_type}: File not found")
    else:
        print("⚠️ No charts were generated")
    
    print("\n🎉 Chart generation test completed!")
    return True

if __name__ == "__main__":
    test_chart_generation() 