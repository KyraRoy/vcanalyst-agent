import logging
import re
from typing import List, Dict, Optional
from models.schemas import Section, Citation, RawDoc
from utils.google_search import search_google
from datetime import datetime

logger = logging.getLogger(__name__)

class MarketMapper:
    def __init__(self):
        # Market size patterns
        self.market_size_patterns = [
            r"(TAM|Total Addressable Market)[^\d]{0,10}(\$?\d+(?:\.\d+)?\s?(million|billion|trillion))",
            r"(market size|industry size)[^\d]{0,20}(\$?\d+(?:\.\d+)?\s?(million|billion))",
            r"(\$?\d+(?:\.\d+)?\s?(million|billion|trillion))\s*(TAM|market|industry)",
            r"(estimated|valued at|worth)\s*(\$?\d+(?:\.\d+)?\s?(million|billion|trillion))\s*(market|industry)",
            r"(\$?\d+(?:\.\d+)?\s?(million|billion|trillion))\s*(dollar|USD)\s*(market|industry)",
        ]
        
        # Competition patterns
        self.competition_patterns = [
            r"(competitors?|alternatives?|competition)\s*(include|are|like|such as)\s*([^\.]+)",
            r"(compete|competing)\s*(with|against)\s*([^\.]+)",
            r"(similar to|like|including)\s*([^\.]+)",
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*[-–]\s*([^\.]+)",
        ]
        
        # Competitor company name patterns
        self.competitor_name_patterns = [
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*(?:Inc|Corp|LLC|Ltd|Company|Co)\b',
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*(?:is|are|was|were)\s*([^\.]+)',
        ]
    
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
    
    def extract_market_size(self, text: str, citations: List[Citation]) -> Optional[Section]:
        """Extract market size information from text"""
        market_sizes = []
        
        for pattern in self.market_size_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) >= 2:
                    # Extract the full sentence containing the match
                    sentence_start = text.rfind('.', 0, match.start()) + 1
                    sentence_end = text.find('.', match.end())
                    if sentence_end == -1:
                        sentence_end = len(text)
                    
                    sentence = text[sentence_start:sentence_end].strip()
                    if len(sentence) > 20:
                        market_sizes.append(sentence)
        
        if market_sizes:
            return Section(
                text=". ".join(market_sizes[:2]),  # Limit to 2 market size mentions
                citations=citations
            )
        
        return None
    
    def extract_competitors(self, text: str, citations: List[Citation]) -> Optional[Section]:
        """Extract competitor information from text"""
        competitors = []
        
        # Look for competitor mentions
        for pattern in self.competition_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) >= 2:
                    # Extract competitor names and context
                    competitor_text = match.group(0)
                    
                    # Look for specific company names in the competitor text
                    company_matches = re.finditer(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', competitor_text)
                    for company_match in company_matches:
                        company_name = company_match.group(1)
                        if len(company_name.split()) >= 2:  # At least 2 words (first + last name)
                            # Get context around the company name
                            context_start = max(0, company_match.start() - 50)
                            context_end = min(len(competitor_text), company_match.end() + 50)
                            context = competitor_text[context_start:context_end].strip()
                            
                            if context not in competitors:
                                competitors.append(context)
        
        # Also look for standalone company mentions with context
        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            if any(word in sentence.lower() for word in ['competitor', 'alternative', 'similar', 'compete']):
                # Extract company names from these sentences
                company_matches = re.finditer(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', sentence)
                for company_match in company_matches:
                    company_name = company_match.group(1)
                    if len(company_name.split()) >= 2:
                        competitors.append(sentence.strip())
        
        if competitors:
            return Section(
                bullets=competitors[:5],  # Limit to 5 competitors
                citations=citations
            )
        
        return None
    
    def map_market(self, company_name: str, docs: List[RawDoc], google_results: List[dict] = None) -> Dict:
        """Map market information from documents and Google search results"""
        logger.info(f"Mapping market for {company_name}")
        
        # Combine all text from documents
        all_text = " ".join([doc.text for doc in docs if doc.text])
        doc_citations = [self.create_citation(doc, doc.text[:200]) for doc in docs if doc.text]
        
        # Combine Google search text if available
        google_text = ""
        google_citations = []
        if google_results:
            google_text = " ".join([result['text'] for result in google_results if result.get('text')])
            google_citations = [self.create_google_citation(result) for result in google_results if result.get('text')]
        
        # Combine all text and citations
        combined_text = f"{all_text} {google_text}".strip()
        all_citations = doc_citations + google_citations
        
        # Extract market information
        market_sizing = self.extract_market_size(combined_text, all_citations)
        competition = self.extract_competitors(combined_text, all_citations)
        
        # Log results
        if market_sizing:
            logger.info(f"Found market sizing data for {company_name}")
        else:
            logger.warning(f"No market sizing data found for {company_name}")
            market_sizing = Section()  # Return empty section instead of None
        
        if competition:
            logger.info(f"Found {len(competition.bullets)} competitors for {company_name}")
        else:
            logger.warning(f"No competition data found for {company_name}")
            competition = Section()  # Return empty section instead of None
        
        return {
            "market_sizing": market_sizing,
            "competition": competition
        }

def map_market(data: dict, docs: List[RawDoc] = None) -> Dict:
    """Main function to map market information"""
    company_name = data.get('company', '')
    
    # Initialize market mapper
    mapper = MarketMapper()
    
    # Get Google search results for market data
    google_results = []
    try:
        queries = [
            f"{company_name} TAM",
            f"{company_name} market size",
            f"{company_name} competitors",
            f"{company_name} alternatives"
        ]
        
        logger.info(f"Performing market-related Google searches for {company_name}")
        google_results = search_google(company_name, queries)
        logger.info(f"Found {len(google_results)} market-related Google search results")
        
    except Exception as e:
        logger.warning(f"Market Google search failed for {company_name}: {e}")
        google_results = []
    
    # Map market information
    return mapper.map_market(company_name, docs or [], google_results)