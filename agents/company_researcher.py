import logging
import os
from typing import List, Optional, Dict, Any
from models.schemas import StructuredCompanyDoc, Section, Citation, RawDoc
from utils.web_scraper import WebScraper
from utils.nlp import NLExtractor
from utils.google_search import search_google
from agents.founder_profiler import evaluate_founder
from agents.market_mapper import map_market
from llm.section_extractor import extract_sections_with_gpt
from agents.pitchdeck_parser import parse_pitch_deck, get_pitch_deck_summary
from datetime import datetime
import re

logger = logging.getLogger(__name__)

def is_high_quality_source(url: str, title: str = "") -> bool:
    """Return True if the source is a high-quality, verifiable source"""
    url_lower = url.lower()
    title_lower = title.lower()
    
    # High-priority sources
    high_priority = [
        'crunchbase.com', 'linkedin.com', 'techcrunch.com', 'forbes.com',
        'bloomberg.com', 'wsj.com', 'reuters.com', 'cnbc.com', 'venturebeat.com',
        'pitchbook.com', 'statista.com', 'gartner.com', 'mckinsey.com',
        'bain.com', 'bcg.com', 'deloitte.com', 'pwc.com', 'ey.com', 'kpmg.com'
    ]
    
    for source in high_priority:
        if source in url_lower:
            return True
    
    # Company official websites
    if any(domain in url_lower for domain in ['.com', '.org', '.io', '.ai', '.tech']):
        if not any(generic in url_lower for generic in ['template', 'example', 'sample']):
            return True
    
    return False

def extract_structured_data_from_sources(sources: List[Dict], company_name: str) -> Dict[str, Any]:
    """
    Extract structured data from verified sources using GPT-4.
    Focus on real, verifiable information only.
    """
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Prepare source data for analysis
        source_text = ""
        for source in sources:
            source_text += f"\nSource: {source.get('url', 'Unknown')}\n"
            source_text += f"Title: {source.get('title', '')}\n"
            source_text += f"Content: {source.get('text', '')[:1000]}...\n\n"
        
        prompt = f"""
        You are a professional VC analyst. Extract ONLY real, verifiable information about {company_name} from the provided sources.
        
        CRITICAL RULES:
        1. ONLY include information that is explicitly stated in the sources
        2. If information is not found, say "No public data available"
        3. NEVER make up names, numbers, or facts
        4. If founders are mentioned, use their real names
        5. If funding is mentioned, use real numbers from Crunchbase/news
        6. If no specific data is found, be honest about it
        
        Sources:
        {source_text}
        
        Extract and return as JSON:
        {{
            "founders": {{
                "names": ["List real founder names if found"],
                "backgrounds": ["List real backgrounds if found"],
                "linkedin_urls": ["List real LinkedIn URLs if found"]
            }},
            "product": {{
                "description": "What the product actually does (from sources)",
                "target_users": "Who it's for (from sources)",
                "features": ["List real features mentioned"]
            }},
            "market": {{
                "size": "Market size if mentioned with real numbers",
                "competitors": ["List real competitors mentioned"],
                "industry": "Industry if mentioned"
            }},
            "funding": {{
                "total_raised": "Real funding amount if mentioned",
                "latest_round": "Latest round details if mentioned",
                "investors": ["List real investors if mentioned"]
            }},
            "traction": {{
                "users": "User numbers if mentioned",
                "revenue": "Revenue if mentioned",
                "growth": "Growth metrics if mentioned"
            }},
            "website": "Company website URL if found",
            "social_media": {{
                "twitter": "Twitter/X handle if found",
                "linkedin": "LinkedIn company page if found"
            }},
            "verification_level": "high/medium/low based on source quality"
        }}
        
        IMPORTANT: If any field cannot be verified from the sources, use "No public data available" or empty arrays.
        """
        
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional VC analyst. Extract only verifiable facts from sources. Never hallucinate or make up information."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,  # Low temperature for factual extraction
            max_tokens=2000
        )
        
        content = response.choices[0].message.content.strip()
        
        # Parse JSON response
        import json
        try:
            data = json.loads(content)
            return data
        except json.JSONDecodeError:
            logger.error(f"Failed to parse GPT response for {company_name}")
            return {}
            
    except Exception as e:
        logger.error(f"Failed to extract structured data for {company_name}: {e}")
        return {}

class CompanyResearcher:
    def __init__(self):
        self.scraper = WebScraper()
        self.nlp = NLExtractor()
    
    def search_verifiable_sources(self, company_name: str) -> List[Dict]:
        """
        Search for verifiable information about the company using specific queries.
        """
        logger.info(f"Searching verifiable sources for {company_name}")
        
        # Specific search queries for real data
        search_queries = [
            f'"{company_name}" official website',
            f'"{company_name}" AI startup',
            f'"{company_name}" founder Crunchbase',
            f'site:linkedin.com "{company_name}"',
            f'site:crunchbase.com "{company_name}"',
            f'site:techcrunch.com "{company_name}"',
            f'site:forbes.com "{company_name}"',
            f'site:bloomberg.com "{company_name}"',
            f'"{company_name}" funding round',
            f'"{company_name}" series A B C',
            f'"{company_name}" CEO founder',
            f'"{company_name}" product launch',
            f'"{company_name}" users customers',
            f'"{company_name}" revenue growth'
        ]
        
        all_sources = []
        
        try:
            # Perform searches
            for query in search_queries:
                try:
                    results = search_google(company_name, [query])
                    if results:
                        # Filter for high-quality sources
                        filtered_results = []
                        for result in results:
                            if is_high_quality_source(result.get('url', ''), result.get('title', '')):
                                filtered_results.append(result)
                        
                        all_sources.extend(filtered_results)
                        logger.info(f"Found {len(filtered_results)} high-quality results for query: {query}")
                        
                except Exception as e:
                    logger.warning(f"Search failed for query '{query}': {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Search failed for {company_name}: {e}")
        
        logger.info(f"Total high-quality sources found for {company_name}: {len(all_sources)}")
        return all_sources
    
    def create_verifiable_memo(self, company_name: str) -> StructuredCompanyDoc:
        """
        Create a verifiable investment memo based on real sources only.
        """
        logger.info(f"Creating verifiable memo for {company_name}")
        
        # Step 1: Search for verifiable sources
        sources = self.search_verifiable_sources(company_name)
        
        if not sources:
            logger.warning(f"No verifiable sources found for {company_name}")
            return self._create_insufficient_data_memo(company_name)
        
        # Step 2: Extract structured data from sources
        structured_data = extract_structured_data_from_sources(sources, company_name)
        
        if not structured_data:
            logger.warning(f"No structured data could be extracted for {company_name}")
            return self._create_insufficient_data_memo(company_name)
        
        # Step 3: Create structured company document
        company_doc = StructuredCompanyDoc(name=company_name)
        
        # Map structured data to memo sections
        self._map_data_to_sections(company_doc, structured_data, sources)
        
        logger.info(f"Verifiable memo created for {company_name}")
        return company_doc
    
    def _create_insufficient_data_memo(self, company_name: str) -> StructuredCompanyDoc:
        """Create a memo indicating insufficient public data"""
        company_doc = StructuredCompanyDoc(name=company_name)
        
        # Create sections indicating insufficient data
        insufficient_text = f"Insufficient public data available for {company_name}. No verifiable information could be found from reliable sources."
        
        company_doc.intro = Section(
            text=insufficient_text,
            bullets=["No public company information available"],
            citations=[]
        )
        
        company_doc.recommendations = Section(
            text=f"Cannot provide investment recommendations for {company_name} due to insufficient public data.",
            bullets=[
                "Insufficient public data for analysis",
                "Recommend conducting primary research",
                "Consider reaching out to company directly"
            ],
            citations=[]
        )
        
        return company_doc
    
    def _map_data_to_sections(self, company_doc: StructuredCompanyDoc, data: Dict, sources: List[Dict]):
        """Map extracted data to memo sections with proper citations"""
        
        # Create citations from sources
        citations = []
        for source in sources:
            citation = Citation(
                source_type=self._determine_source_type(source.get('url', '')),
                url=source.get('url', ''),
                title=source.get('title', ''),
                timestamp=datetime.now()
            )
            citations.append(citation)
        
        # Map founders data
        if data.get('founders'):
            founders_text = ""
            if data['founders'].get('names'):
                founders_text += f"Founders: {', '.join(data['founders']['names'])}. "
            if data['founders'].get('backgrounds'):
                founders_text += f"Backgrounds: {'; '.join(data['founders']['backgrounds'])}"
            
            if founders_text:
                company_doc.team = Section(
                    text=founders_text,
                    bullets=data['founders'].get('names', []),
                    citations=citations
                )
        
        # Map product data
        if data.get('product'):
            product_text = ""
            if data['product'].get('description'):
                product_text += f"{data['product']['description']}. "
            if data['product'].get('target_users'):
                product_text += f"Target users: {data['product']['target_users']}"
            
            if product_text:
                company_doc.product = Section(
                    text=product_text,
                    bullets=data['product'].get('features', []),
                    citations=citations
                )
        
        # Map market data
        if data.get('market'):
            market_text = ""
            if data['market'].get('size'):
                market_text += f"Market size: {data['market']['size']}. "
            if data['market'].get('industry'):
                market_text += f"Industry: {data['market']['industry']}"
            
            if market_text:
                company_doc.market = Section(
                    text=market_text,
                    bullets=data['market'].get('competitors', []),
                    citations=citations
                )
        
        # Map funding data
        if data.get('funding'):
            funding_text = ""
            if data['funding'].get('total_raised'):
                funding_text += f"Total raised: {data['funding']['total_raised']}. "
            if data['funding'].get('latest_round'):
                funding_text += f"Latest round: {data['funding']['latest_round']}"
            
            if funding_text:
                company_doc.financials = Section(
                    text=funding_text,
                    bullets=data['funding'].get('investors', []),
                    citations=citations
                )
        
        # Map traction data
        if data.get('traction'):
            traction_text = ""
            if data['traction'].get('users'):
                traction_text += f"Users: {data['traction']['users']}. "
            if data['traction'].get('revenue'):
                traction_text += f"Revenue: {data['traction']['revenue']}"
            
            if traction_text:
                company_doc.traction = Section(
                    text=traction_text,
                    bullets=[f"Growth: {data['traction'].get('growth', 'N/A')}"],
                    citations=citations
                )
        
        # Create executive summary
        summary_text = f"{company_name} is a company with limited public information available. "
        if data.get('product', {}).get('description'):
            summary_text += data['product']['description']
        
        company_doc.intro = Section(
            text=summary_text,
            bullets=[f"Verification level: {data.get('verification_level', 'unknown')}"],
            citations=citations
        )
    
    def _determine_source_type(self, url: str) -> str:
        """Determine the source type based on URL"""
        url_lower = url.lower()
        
        if 'crunchbase.com' in url_lower:
            return 'Crunchbase'
        elif 'linkedin.com' in url_lower:
            return 'LinkedIn'
        elif 'techcrunch.com' in url_lower:
            return 'TechCrunch'
        elif 'forbes.com' in url_lower:
            return 'Forbes'
        elif 'bloomberg.com' in url_lower:
            return 'Bloomberg'
        elif 'wsj.com' in url_lower:
            return 'Wall Street Journal'
        elif 'reuters.com' in url_lower:
            return 'Reuters'
        elif 'cnbc.com' in url_lower:
            return 'CNBC'
        elif 'venturebeat.com' in url_lower:
            return 'VentureBeat'
        elif 'pitchbook.com' in url_lower:
            return 'PitchBook'
        else:
            # Extract domain name
            from urllib.parse import urlparse
            try:
                domain = urlparse(url).netloc
                if domain:
                    return f"{domain.title()}"
                else:
                    return "Web Source"
            except:
                return "Web Source"
    
    def analyze_company(self, company_name: str, website: str = None, founder_name: str = None) -> StructuredCompanyDoc:
        """Main method to analyze a company with focus on verifiable data"""
        logger.info(f"Starting verifiable analysis of {company_name}")
        
        # Use the new verifiable memo creation
        return self.create_verifiable_memo(company_name)

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
