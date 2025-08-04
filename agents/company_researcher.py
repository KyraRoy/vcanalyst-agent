import logging
from typing import List, Optional
from models.schemas import StructuredCompanyDoc, Section, Citation, RawDoc
from utils.web_scraper import WebScraper
from utils.nlp import NLExtractor
from utils.google_search import search_google
from agents.founder_profiler import evaluate_founder
from agents.market_mapper import map_market
from llm.section_extractor import extract_sections_with_gpt
from agents.pitchdeck_parser import parse_pitch_deck, get_pitch_deck_summary
from datetime import datetime

logger = logging.getLogger(__name__)

def is_valid_source(doc: RawDoc, company_name: str) -> bool:
    """Return True if the doc is specifically about the target company, not a general example/template."""
    if not doc or not doc.text:
        return False
    company = company_name.lower().strip()
    text = doc.text.lower()[:500] if doc.text else ""
    title = doc.title.lower() if doc.title else ""
    # Must mention company in first 500 chars or in title
    if company not in text and company not in title:
        return False
    # Reject if doc is about example pitch decks or other companies
    blacklist = ["dropbox", "airbnb", "uber", "wework", "buffer", "parsec"]
    for bad in blacklist:
        if bad in text:
            return False
    # Reject if doc is a general template or how-to
    generic_phrases = ["example", "template", "how to make"]
    for phrase in generic_phrases:
        if phrase in text or phrase in title:
            return False
    return True

def is_valid_google_result(result: dict, company_name: str) -> bool:
    """Return True if the Google result is specifically about the target company, not a general example/template."""
    if not result or not result.get('text'):
        return False
    company = company_name.lower().strip()
    text = result.get('text', '').lower()[:500]
    title = result.get('title', '').lower()
    # Must mention company in first 500 chars or in title
    if company not in text and company not in title:
        return False
    # Reject if result is about example pitch decks or other companies
    blacklist = ["dropbox", "airbnb", "uber", "wework", "buffer", "parsec"]
    for bad in blacklist:
        if bad in text:
            return False
    # Reject if result is a general template or how-to
    generic_phrases = ["example", "template", "how to make"]
    for phrase in generic_phrases:
        if phrase in text or phrase in title:
            return False
    return True

class CompanyResearcher:
    def __init__(self):
        self.scraper = WebScraper()
        self.nlp = NLExtractor()
    
    def create_citation(self, raw_doc: RawDoc, snippet: str) -> Citation:
        """Create a citation from a raw document"""
        return Citation(
            url=raw_doc.url,
            snippet=snippet[:200] + "..." if len(snippet) > 200 else snippet,
            source_type=raw_doc.source_type,
            timestamp=raw_doc.timestamp
        )
    
    def create_google_citation(self, result: dict) -> Citation:
        """Create a citation from a Google search result"""
        return Citation(
            url=result['url'],
            snippet=result['snippet'][:200] + "..." if len(result['snippet']) > 200 else result['snippet'],
            source_type="google_search",
            timestamp=datetime.now()
        )
    
    def extract_from_docs(self, docs: List[RawDoc], google_results: List[dict], founder_data: dict, market_data: dict, company_name: str) -> StructuredCompanyDoc:
        """Extract structured information from raw documents, Google results, founder data, and market data"""
        company_doc = StructuredCompanyDoc(name=company_name)
        
        # Filter docs and google_results for relevance
        filtered_docs = [doc for doc in docs if is_valid_source(doc, company_name)]
        filtered_google_results = [result for result in google_results if is_valid_google_result(result, company_name)]
        
        # Combine all docs for structured extraction
        all_docs = filtered_docs + filtered_google_results
        
        # Try GPT-4 extraction first, fallback to rule-based NLP
        try:
            logger.info(f"Attempting GPT-4 extraction for {company_name}")
            structured_sections = extract_sections_with_gpt(company_name, all_docs)
            
            if structured_sections:
                logger.info(f"GPT-4 extraction successful for {company_name}")
                # Apply structured sections to company_doc
                for section_name, section_obj in structured_sections.items():
                    if hasattr(company_doc, section_name):
                        setattr(company_doc, section_name, section_obj)
            else:
                logger.warning(f"GPT-4 extraction returned no results for {company_name}, falling back to NLP")
                # Fallback to rule-based NLP
                structured_sections = self.nlp.extract_structured_fields(all_docs, company_name)
                for section_name, section_obj in structured_sections.items():
                    if hasattr(company_doc, section_name):
                        setattr(company_doc, section_name, section_obj)
                        
        except Exception as e:
            logger.warning(f"GPT-4 extraction failed for {company_name}: {e}, falling back to NLP")
            # Fallback to rule-based NLP
            structured_sections = self.nlp.extract_structured_fields(all_docs, company_name)
            for section_name, section_obj in structured_sections.items():
                if hasattr(company_doc, section_name):
                    setattr(company_doc, section_name, section_obj)
        
        # Use dynamic founder profiler for team information
        from agents.founder_profiler import get_founder_team_info
        company_doc.team = get_founder_team_info(company_name)
        
        # Use market mapper for market and competition data
        company_doc.market = market_data.get('market_sizing', Section())
        company_doc.competitors = market_data.get('competition', Section())
        
        # Set missing fields
        company_doc.missing_fields = company_doc.get_missing_fields()
        return company_doc
    
    def analyze_company(self, company_name: str, website: str, founder_name: str = None) -> StructuredCompanyDoc:
        """Main method to analyze a company with website, Google search, founder data, and market data"""
        logger.info(f"Starting analysis of {company_name} at {website}")
        
        # Step 1: Scrape company website
        docs = self.scraper.scrape_company_website(website)
        
        if not docs:
            logger.warning(f"No documents could be scraped for {company_name}")
            docs = []
        
        # Step 2: Perform Google searches for external content
        google_results = []
        try:
            queries = [
                f"{company_name} traction",
                f"{company_name} funding",
                f"{company_name} MAU",
                f"{company_name} team",
                f"{company_name} product",
                f"{company_name} pricing",
                f"{company_name} press release"
            ]
            
            logger.info(f"Performing Google searches for {company_name}")
            google_results = search_google(company_name, queries)
            logger.info(f"Found {len(google_results)} Google search results")
            
        except Exception as e:
            logger.warning(f"Google search failed for {company_name}: {e}")
            google_results = []
        
        # Step 3: Get founder and team information (includes LinkedIn data)
        founder_data = {}
        try:
            logger.info(f"Evaluating founder and team for {company_name}")
            founder_data = evaluate_founder(founder_name or "Unknown", company_name)
            logger.info(f"Founder evaluation complete for {company_name}")
            
        except Exception as e:
            logger.warning(f"Founder evaluation failed for {company_name}: {e}")
            founder_data = {}
        
        # Step 4: Get market and competition data
        market_data = {}
        try:
            logger.info(f"Mapping market and competition for {company_name}")
            market_data = map_market({"company": company_name}, docs)
            logger.info(f"Market mapping complete for {company_name}")
            
        except Exception as e:
            logger.warning(f"Market mapping failed for {company_name}: {e}")
            market_data = {}
        
        # Step 5: Extract structured information from all sources
        company_doc = self.extract_from_docs(docs, google_results, founder_data, market_data, company_name)
        company_doc.website = website
        
        logger.info(f"Analysis complete for {company_name}. Found {len(company_doc.get_populated_sections())} populated sections.")
        
        return company_doc

    def analyze_pitch_deck(self, pdf_path: str, company_name: str = None) -> StructuredCompanyDoc:
        """
        Analyze a pitch deck PDF and extract structured investment memo data.
        
        Args:
            pdf_path: Path to the pitch deck PDF
            company_name: Optional company name for context
            
        Returns:
            StructuredCompanyDoc with extracted pitch deck data
        """
        logger.info(f"Starting pitch deck analysis for {pdf_path}")
        
        # Parse the pitch deck
        pitch_deck_sections = parse_pitch_deck(pdf_path)
        
        if not pitch_deck_sections:
            logger.warning("No content could be extracted from the pitch deck")
            return StructuredCompanyDoc(name=company_name or "Unknown Company")
        
        # Create a structured company document from pitch deck data
        company_doc = StructuredCompanyDoc(name=company_name or "Unknown Company")
        
        # Apply pitch deck sections to the company document
        for section_name, section_obj in pitch_deck_sections.items():
            if hasattr(company_doc, section_name):
                setattr(company_doc, section_name, section_obj)
        
        # Set missing fields
        company_doc.missing_fields = company_doc.get_missing_fields()
        
        logger.info(f"Pitch deck analysis complete. Found {len(company_doc.get_populated_sections())} populated sections.")
        
        return company_doc
