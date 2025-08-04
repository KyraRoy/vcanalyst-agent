import json
import os
import logging
from agents.company_researcher import CompanyResearcher
from agents.market_mapper import map_market
from agents.founder_profiler import evaluate_founder
from agents.memo_generator import generate_memo
from models.schemas import StructuredCompanyDoc
from utils.pdf_generator import generate_pdf
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_main_agent():
    # Load input data
    with open('data/test_input.json', 'r') as f:
        data = json.load(f)

    # Initialize company researcher
    researcher = CompanyResearcher()
    
    # Analyze company with evidence-based extraction (includes founder name)
    company_doc = researcher.analyze_company(
        data['company'], 
        data['website'], 
        data.get('founder')  # Pass founder name if available
    )
    
    # Generate memo with conditional sections
    memo = generate_memo(company_doc)

    # Print memo
    print(memo)

    # Save memo as text
    os.makedirs('data/memos', exist_ok=True)
    memo_path = os.path.join('data/memos', f"{data['company']}_investment_memo.txt")
    with open(memo_path, 'w') as f:
        f.write(memo)
    print(f"Memo saved to {memo_path}")
    
    # Save structured data as JSON for analysis
    json_path = os.path.join('data/memos', f"{data['company']}_structured_data.json")
    with open(json_path, 'w') as f:
        f.write(company_doc.model_dump_json(indent=2))
    print(f"Structured data saved to {json_path}")

        # Generate PDF with charts
    pdf_path = os.path.join('data/memos', f"{data['company'].replace(' ', '_')}_memo.pdf")
    from utils.pdf_generator import generate_pdf_with_charts
    generate_pdf_with_charts(memo, pdf_path, company_doc, data['company'])
    print(f"PDF with charts saved to {pdf_path}")

if __name__ == "__main__":
    run_main_agent()
