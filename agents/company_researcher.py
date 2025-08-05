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
    
    # Early-stage startup sources
    startup_sources = [
        'producthunt.com', 'hackernews.com', 'reddit.com', 'twitter.com', 'x.com',
        'medium.com', 'substack.com', 'github.com', 'angel.co', 'angellist.com',
        'ycombinator.com', 'demo-day', 'startup-school', 'indiehackers.com',
        'makers.com', 'nomadlist.com', 'remoteok.com', 'wework.com', 'techstars.com'
    ]
    
    for source in startup_sources:
        if source in url_lower:
            return True
    
    return False

def is_acceptable_source(url: str, title: str = "", company_name: str = "") -> bool:
    """Return True if the source is acceptable for early-stage startups"""
    url_lower = url.lower()
    title_lower = title.lower()
    company_lower = company_name.lower()
    
    # Must mention the company name
    if company_name and company_lower not in url_lower and company_lower not in title_lower:
        return False
    
    # Reject obvious spam or irrelevant sites
    spam_domains = [
        'spam.com', 'clickbait.com', 'fake-news.com', 'template.com',
        'example.com', 'sample.com', 'test.com', 'placeholder.com'
    ]
    
    for spam in spam_domains:
        if spam in url_lower:
            return False
    
    # Accept most domains that mention the company
    return True

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
        5. If funding is mentioned, use real numbers from sources
        6. If no specific data is found, be honest about it
        7. For early-stage startups, accept information from founder blogs, social media, and community platforms
        8. Be flexible with source quality for startups that may not have major news coverage
        
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
                "features": ["List real features mentioned"],
                "stage": "MVP/Beta/Alpha/Launched if mentioned"
            }},
            "market": {{
                "size": "Market size if mentioned with real numbers",
                "competitors": ["List real competitors mentioned"],
                "industry": "Industry if mentioned",
                "problem": "Problem they're solving if mentioned"
            }},
            "funding": {{
                "total_raised": "Real funding amount if mentioned",
                "latest_round": "Latest round details if mentioned",
                "investors": ["List real investors if mentioned"],
                "stage": "Pre-seed/Seed/Series A/etc if mentioned"
            }},
            "traction": {{
                "users": "User numbers if mentioned",
                "revenue": "Revenue if mentioned",
                "growth": "Growth metrics if mentioned",
                "customers": "Customer count if mentioned",
                "downloads": "Download numbers if mentioned"
            }},
            "website": "Company website URL if found",
            "social_media": {{
                "twitter": "Twitter/X handle if found",
                "linkedin": "LinkedIn company page if found",
                "github": "GitHub repo if found",
                "producthunt": "Product Hunt page if found"
            }},
            "verification_level": "high/medium/low based on source quality",
            "startup_stage": "early-stage/established based on available data"
        }}
        
        IMPORTANT: 
        - If any field cannot be verified from the sources, use "No public data available" or empty arrays
        - For early-stage startups, accept information from founder posts, social media, and community platforms
        - Be honest about data quality and source reliability
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
        
        # Comprehensive search queries for both established and early-stage companies
        search_queries = [
            # Official sources
            f'"{company_name}" official website',
            f'"{company_name}" company',
            f'"{company_name}" startup',
            
            # Founder and team
            f'"{company_name}" founder',
            f'"{company_name}" CEO',
            f'"{company_name}" team',
            f'"{company_name}" founder Crunchbase',
            f'"{company_name}" founder LinkedIn',
            
            # Platform-specific searches
            f'site:linkedin.com "{company_name}"',
            f'site:crunchbase.com "{company_name}"',
            f'site:producthunt.com "{company_name}"',
            f'site:angel.co "{company_name}"',
            f'site:angellist.com "{company_name}"',
            f'site:ycombinator.com "{company_name}"',
            f'site:techstars.com "{company_name}"',
            f'site:medium.com "{company_name}"',
            f'site:substack.com "{company_name}"',
            f'site:github.com "{company_name}"',
            f'site:twitter.com "{company_name}"',
            f'site:x.com "{company_name}"',
            f'site:reddit.com "{company_name}"',
            f'site:hackernews.com "{company_name}"',
            
            # News and media
            f'site:techcrunch.com "{company_name}"',
            f'site:forbes.com "{company_name}"',
            f'site:bloomberg.com "{company_name}"',
            f'site:venturebeat.com "{company_name}"',
            f'site:wsj.com "{company_name}"',
            f'site:reuters.com "{company_name}"',
            f'site:cnbc.com "{company_name}"',
            
            # Product and business
            f'"{company_name}" product',
            f'"{company_name}" launch',
            f'"{company_name}" demo',
            f'"{company_name}" beta',
            f'"{company_name}" alpha',
            f'"{company_name}" MVP',
            f'"{company_name}" minimum viable product',
            
            # Funding and investment
            f'"{company_name}" funding',
            f'"{company_name}" investment',
            f'"{company_name}" seed',
            f'"{company_name}" series A',
            f'"{company_name}" angel',
            f'"{company_name}" pre-seed',
            f'"{company_name}" round',
            
            # Traction and metrics
            f'"{company_name}" users',
            f'"{company_name}" customers',
            f'"{company_name}" revenue',
            f'"{company_name}" growth',
            f'"{company_name}" traction',
            f'"{company_name}" metrics',
            
            # Industry and market
            f'"{company_name}" market',
            f'"{company_name}" industry',
            f'"{company_name}" competitors',
            f'"{company_name}" competition',
            
            # Social and community
            f'"{company_name}" community',
            f'"{company_name}" users',
            f'"{company_name}" feedback',
            f'"{company_name}" reviews',
            f'"{company_name}" testimonials'
        ]
        
        all_sources = []
        high_quality_sources = []
        
        try:
            # Perform searches
            for query in search_queries:
                try:
                    results = search_google(company_name, [query])
                    if results:
                        # Separate high-quality and acceptable sources
                        for result in results:
                            if is_high_quality_source(result.get('url', ''), result.get('title', '')):
                                high_quality_sources.append(result)
                            elif is_acceptable_source(result.get('url', ''), result.get('title', ''), company_name):
                                all_sources.append(result)
                        
                        logger.info(f"Found {len(results)} results for query: {query}")
                        
                except Exception as e:
                    logger.warning(f"Search failed for query '{query}': {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Search failed for {company_name}: {e}")
        
        # Prioritize high-quality sources but include acceptable ones
        final_sources = high_quality_sources + all_sources
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_sources = []
        for source in final_sources:
            url = source.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_sources.append(source)
        
        logger.info(f"Total sources found for {company_name}: {len(unique_sources)} (High quality: {len(high_quality_sources)})")
        return unique_sources
    
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
        insufficient_text = f"Insufficient public data available for {company_name}. This could be an early-stage startup with limited online presence, or the company may be using a different name."
        
        company_doc.intro = Section(
            text=insufficient_text,
            bullets=[
                "No public company information available",
                "May be an early-stage startup",
                "Consider reaching out to company directly"
            ],
            citations=[]
        )
        
        company_doc.recommendations = Section(
            text=f"Cannot provide investment recommendations for {company_name} due to insufficient public data. This is common for early-stage startups that haven't yet established significant online presence.",
            bullets=[
                "Insufficient public data for analysis",
                "Common for early-stage startups",
                "Recommend conducting primary research",
                "Consider reaching out to company directly",
                "Check if company uses different name"
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
        summary_text = f"{company_name} "
        
        # Determine if it's an early-stage startup
        startup_stage = data.get('startup_stage', 'unknown')
        verification_level = data.get('verification_level', 'unknown')
        
        if startup_stage == 'early-stage':
            summary_text += "appears to be an early-stage startup. "
        elif startup_stage == 'established':
            summary_text += "appears to be an established company. "
        else:
            summary_text += "is a company with limited public information available. "
        
        if data.get('product', {}).get('description'):
            summary_text += data['product']['description']
        
        # Add verification context
        verification_bullets = [f"Verification level: {verification_level}"]
        if startup_stage != 'unknown':
            verification_bullets.append(f"Startup stage: {startup_stage}")
        
        company_doc.intro = Section(
            text=summary_text,
            bullets=verification_bullets,
            citations=citations
        )
        
        # Create recommendations based on data quality
        if verification_level == 'high':
            rec_text = f"Based on high-quality sources, {company_name} shows potential for investment consideration."
        elif verification_level == 'medium':
            rec_text = f"Based on available sources, {company_name} shows some potential but more research is recommended."
        else:
            rec_text = f"Limited data available for {company_name}. Recommend conducting primary research before making investment decisions."
        
        company_doc.recommendations = Section(
            text=rec_text,
            bullets=[
                f"Data quality: {verification_level}",
                f"Startup stage: {startup_stage}",
                "Recommend conducting additional research",
                "Consider reaching out to company directly"
            ],
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
