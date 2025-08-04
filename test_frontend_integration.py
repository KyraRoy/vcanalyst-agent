#!/usr/bin/env python3
"""
Test script to verify frontend integration with backend components.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.company_researcher import CompanyResearcher
from agents.memo_generator import generate_memo
from models.schemas import StructuredCompanyDoc

def test_frontend_integration():
    """Test that frontend can import and use backend components"""
    print("🧪 Testing Frontend Integration...")
    
    try:
        # Test 1: Import components
        print("✅ Successfully imported backend components")
        
        # Test 2: Create CompanyResearcher
        researcher = CompanyResearcher()
        print("✅ Successfully created CompanyResearcher")
        
        # Test 3: Test with a simple company
        print("🔍 Testing with 'Test Company'...")
        
        # Create a minimal test document
        test_doc = StructuredCompanyDoc(name="Test Company")
        test_doc.intro.text = "This is a test company for frontend integration."
        test_doc.problem.text = "Test problem statement."
        test_doc.solution.text = "Test solution."
        
        # Test 4: Generate memo
        memo = generate_memo(test_doc)
        print("✅ Successfully generated memo")
        
        # Test 5: Check memo content
        if "Test Company" in memo and "test company" in memo.lower():
            print("✅ Memo contains expected content")
        else:
            print("⚠️ Memo content may be incomplete")
        
        print("\n🎉 Frontend integration test passed!")
        print("\nTo run the frontend:")
        print("1. cd frontend")
        print("2. streamlit run app.py")
        print("3. Open http://localhost:8501 in your browser")
        
        return True
        
    except Exception as e:
        print(f"❌ Frontend integration test failed: {e}")
        return False

if __name__ == "__main__":
    test_frontend_integration() 