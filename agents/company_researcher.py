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
        You are a professional VC analyst. Extract ONLY real, verifiable information about {company_name} from the provided sources and generate natural language summaries.
        
        CRITICAL ANTI-HALLUCINATION RULES:
        1. ONLY include information that is explicitly stated in the sources
        2. If information is not found, say "No public data available" or "Limited information available"
        3. NEVER make up names, numbers, or facts
        4. NEVER use placeholder names like "Jane Doe", "John Smith", or generic names
        5. NEVER make up funding amounts, dates, or metrics
        6. NEVER make up company history, milestones, or achievements
        7. Use the company's own words when describing their product/mission
        8. If funding is mentioned, use real numbers from sources
        9. If no specific data is found, be honest about it
        10. Generate natural language summaries of the real information found
        11. Be explicit about what information is limited or unavailable
        12. If you cannot verify a fact, DO NOT include it
        
        Sources:
        {source_text}
        
        Extract and return as JSON:
        {{
            "company_description": {{
                "official_description": "Company's own description from their website (if found)",
                "mission_statement": "Company's mission if stated (if found)",
                "website_url": "Official website URL if found"
            }},
            "team": {{
                "founders": ["ONLY real founder names if explicitly found"],
                "team_members": ["ONLY real team member names if explicitly found"],
                "backgrounds": ["ONLY real backgrounds if explicitly found"],
                "linkedin_urls": ["ONLY real LinkedIn URLs if found"]
            }},
            "product": {{
                "description": "What the product actually does (in company's own words, if found)",
                "problem_solved": "Problem they solve (in company's own words, if found)",
                "features": ["ONLY real features explicitly mentioned"],
                "target_users": "Who it's for (if explicitly mentioned)"
            }},
            "funding": {{
                "total_raised": "ONLY real funding amount if explicitly mentioned",
                "latest_round": "ONLY latest round details if explicitly mentioned",
                "investors": ["ONLY real investors if explicitly mentioned"],
                "funding_status": "Publicly available funding info only"
            }},
            "partnerships": {{
                "partners": ["ONLY real partners if explicitly mentioned"],
                "partnerships": ["ONLY real partnerships if explicitly mentioned"]
            }},
            "competitors": {{
                "mentioned_competitors": ["ONLY competitors the company explicitly mentions"],
                "implied_competitors": ["ONLY competitors implied from context"],
                "market_position": "How company positions itself (if explicitly mentioned)"
            }},
            "social_media": {{
                "linkedin": "LinkedIn company page if found",
                "twitter": "Twitter/X handle if found",
                "website": "Official website if found"
            }},
            "data_quality": {{
                "verification_level": "high/medium/low based on source quality",
                "missing_information": ["List of information that is not available"],
                "sources_used": ["List of source types used"],
                "fake_data_detected": "yes/no - whether any fake data was detected"
            }}
        }}
        
        CRITICAL: 
        - If any field cannot be verified from the sources, use "No public data available" or empty arrays
        - Use the company's own words when describing their product and mission
        - Be explicit about what information is limited or unavailable
        - Generate natural language summaries of the real information found
        - Do not fill in gaps with assumptions or fake data
        - If you see placeholder names like "Jane Doe" or generic information, mark it as fake data
        - Only include information that is explicitly stated in the provided sources
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
            
            # Detect and clean fake data
            data = detect_fake_data(data)
            
            return data
        except json.JSONDecodeError:
            logger.error(f"Failed to parse GPT response for {company_name}")
            return {}
            
    except Exception as e:
        logger.error(f"Failed to extract structured data for {company_name}: {e}")
        return {}

def detect_fake_data(data: Dict) -> Dict:
    """Detect and clean fake data from GPT response"""
    
    # Common fake names and patterns
    fake_names = [
        "jane doe", "john smith", "jane smith", "john doe", "jane johnson", "john johnson",
        "jane williams", "john williams", "jane brown", "john brown", "jane jones", "john jones",
        "jane garcia", "john garcia", "jane miller", "john miller", "jane davis", "john davis",
        "jane rodriguez", "john rodriguez", "jane martinez", "john martinez", "jane hernandez",
        "john hernandez", "jane lopez", "john lopez", "jane gonzalez", "john gonzalez",
        "jane wilson", "john wilson", "jane anderson", "john anderson", "jane thomas",
        "john thomas", "jane taylor", "john taylor", "jane moore", "john moore",
        "jane jackson", "john jackson", "jane martin", "john martin", "jane lee",
        "john lee", "jane perez", "john perez", "jane thompson", "john thompson",
        "jane white", "john white", "jane harris", "john harris", "jane sanchez",
        "john sanchez", "jane clark", "john clark", "jane ramirez", "john ramirez",
        "jane lewis", "john lewis", "jane robinson", "john robinson", "jane walker",
        "john walker", "jane young", "john young", "jane allen", "john allen",
        "jane king", "john king", "jane wright", "john wright", "jane scott",
        "john scott", "jane torres", "john torres", "jane nguyen", "john nguyen",
        "jane hill", "john hill", "jane flores", "john flores", "jane green",
        "john green", "jane adams", "john adams", "jane nelson", "john nelson",
        "jane baker", "john baker", "jane hall", "john hall", "jane rivera",
        "john rivera", "jane campbell", "john campbell", "jane mitchell",
        "john mitchell", "jane carter", "john carter", "jane roberts", "john roberts"
    ]
    
    # Common fake patterns
    fake_patterns = [
        "founded in 2018", "founded in 2019", "founded in 2020", "founded in 2021", "founded in 2022",
        "raised $30M", "raised $50M", "raised $100M", "raised $200M", "raised $500M",
        "series a", "series b", "series c", "seed round", "pre-seed",
        "headquartered in san francisco", "headquartered in new york", "headquartered in silicon valley",
        "ceo jane doe", "cto john smith", "founder jane doe", "founder john smith",
        "phd in machine learning", "phd in computer science", "phd in artificial intelligence",
        "previously worked at google", "previously worked at facebook", "previously worked at apple",
        "previously worked at microsoft", "previously worked at amazon", "previously worked at tesla"
    ]
    
    cleaned_data = data.copy()
    fake_detected = False
    
    # Check team names
    if 'team' in cleaned_data:
        if 'founders' in cleaned_data['team']:
            founders = cleaned_data['team']['founders']
            if isinstance(founders, list):
                for founder in founders:
                    if isinstance(founder, str) and founder.lower() in fake_names:
                        fake_detected = True
                        cleaned_data['team']['founders'] = []
                        break
        
        if 'team_members' in cleaned_data['team']:
            team_members = cleaned_data['team']['team_members']
            if isinstance(team_members, list):
                for member in team_members:
                    if isinstance(member, str) and member.lower() in fake_names:
                        fake_detected = True
                        cleaned_data['team']['team_members'] = []
                        break
    
    # Check funding amounts
    if 'funding' in cleaned_data:
        if 'total_raised' in cleaned_data['funding']:
            total_raised = cleaned_data['funding']['total_raised']
            if isinstance(total_raised, str):
                # Check for common fake funding patterns
                if any(pattern in total_raised.lower() for pattern in ["$30m", "$50m", "$100m", "$200m", "$500m"]):
                    fake_detected = True
                    cleaned_data['funding']['total_raised'] = "No public data available"
    
    # Check company description for fake patterns
    if 'company_description' in cleaned_data:
        if 'official_description' in cleaned_data['company_description']:
            desc = cleaned_data['company_description']['official_description']
            if isinstance(desc, str):
                if any(pattern in desc.lower() for pattern in fake_patterns):
                    fake_detected = True
                    cleaned_data['company_description']['official_description'] = "Limited public data available"
    
    # Update data quality
    if 'data_quality' in cleaned_data:
        cleaned_data['data_quality']['fake_data_detected'] = "yes" if fake_detected else "no"
        if fake_detected:
            cleaned_data['data_quality']['verification_level'] = "low"
    
    return cleaned_data

class CompanyResearcher:
    def __init__(self):
        self.scraper = WebScraper()
        self.nlp = NLExtractor()
    
    def search_verifiable_sources(self, company_name: str) -> List[Dict]:
        """
        Search for verifiable information about the company using specific queries.
        """
        logger.info(f"Searching verifiable sources for {company_name}")
        
        # Focused search queries for real company information
        search_queries = [
            # Official company sources
            f'"{company_name}" official website',
            f'"{company_name}" company',
            f'"{company_name}" about us',
            f'"{company_name}" mission',
            
            # Social media and professional networks
            f'site:linkedin.com "{company_name}"',
            f'site:twitter.com "{company_name}"',
            f'site:x.com "{company_name}"',
            f'"{company_name}" LinkedIn',
            f'"{company_name}" Twitter',
            
            # Tech and startup news
            f'site:techcrunch.com "{company_name}"',
            f'site:venturebeat.com "{company_name}"',
            f'site:producthunt.com "{company_name}"',
            f'site:angel.co "{company_name}"',
            f'site:angellist.com "{company_name}"',
            f'site:ycombinator.com "{company_name}"',
            f'site:techstars.com "{company_name}"',
            
            # Product and business information
            f'"{company_name}" product',
            f'"{company_name}" what we do',
            f'"{company_name}" problem we solve',
            f'"{company_name}" features',
            f'"{company_name}" how it works',
            
            # Team and founders
            f'"{company_name}" team',
            f'"{company_name}" founders',
            f'"{company_name}" CEO',
            f'"{company_name}" about team',
            
            # Funding and partnerships (only if publicly available)
            f'"{company_name}" funding',
            f'"{company_name}" investment',
            f'"{company_name}" partners',
            f'"{company_name}" partnerships',
            f'site:crunchbase.com "{company_name}"',
            
            # Competitors and market
            f'"{company_name}" competitors',
            f'"{company_name}" vs',
            f'"{company_name}" alternative',
            f'"{company_name}" market'
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
        """Map extracted data to memo sections with proper citations and natural language summaries"""
        
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
        
        # Create natural language summary based on real information
        summary_parts = []
        
        # Company description
        if data.get('company_description'):
            if data['company_description'].get('official_description'):
                summary_parts.append(f"{data['company_description']['official_description']}")
            if data['company_description'].get('mission_statement'):
                summary_parts.append(f"Their mission is: {data['company_description']['mission_statement']}")
        
        # Team information
        if data.get('team'):
            team_info = []
            if data['team'].get('founders'):
                team_info.append(f"Founded by {', '.join(data['team']['founders'])}")
            if data['team'].get('team_members'):
                team_info.append(f"Team includes {', '.join(data['team']['team_members'])}")
            if team_info:
                summary_parts.append(' '.join(team_info))
        
        # Product information
        if data.get('product'):
            product_info = []
            if data['product'].get('description'):
                product_info.append(f"They build {data['product']['description']}")
            if data['product'].get('problem_solved'):
                product_info.append(f"to solve {data['product']['problem_solved']}")
            if product_info:
                summary_parts.append(' '.join(product_info))
        
        # Funding information (only if publicly available)
        if data.get('funding'):
            funding_info = []
            if data['funding'].get('total_raised'):
                funding_info.append(f"They have raised {data['funding']['total_raised']}")
            if data['funding'].get('latest_round'):
                funding_info.append(f"with their latest round being {data['funding']['latest_round']}")
            if funding_info:
                summary_parts.append(' '.join(funding_info))
        
        # Create executive summary
        if summary_parts:
            summary_text = f"{company_doc.name} is a company that {' '.join(summary_parts)}."
        else:
            summary_text = f"{company_doc.name} has limited public information available. No verifiable details could be found from reliable sources."
        
        # Add data quality context
        data_quality = data.get('data_quality', {})
        verification_level = data_quality.get('verification_level', 'unknown')
        missing_info = data_quality.get('missing_information', [])
        fake_detected = data_quality.get('fake_data_detected', 'no')
        
        quality_bullets = [f"Data quality: {verification_level}"]
        if missing_info:
            quality_bullets.append(f"Missing information: {', '.join(missing_info)}")
        if fake_detected == 'yes':
            quality_bullets.append("⚠️ Fake data detected and removed")
        
        company_doc.intro = Section(
            text=summary_text,
            bullets=quality_bullets,
            citations=citations
        )
        
        # Create recommendations based on data quality
        if fake_detected == 'yes':
            rec_text = f"⚠️ Fake data was detected in the analysis of {company_doc.name}. Recommend conducting primary research to verify all information."
        elif verification_level == 'high':
            rec_text = f"Based on high-quality sources, {company_doc.name} shows potential for investment consideration."
        elif verification_level == 'medium':
            rec_text = f"Based on available sources, {company_doc.name} shows some potential but more research is recommended."
        else:
            rec_text = f"Limited data available for {company_doc.name}. Recommend conducting primary research before making investment decisions."
        
        company_doc.recommendations = Section(
            text=rec_text,
            bullets=[
                f"Data quality: {verification_level}",
                "Recommend conducting additional research",
                "Consider reaching out to company directly"
            ],
            citations=citations
        )
        
        # Map team data
        if data.get('team'):
            team_text = ""
            if data['team'].get('founders'):
                team_text += f"Founders: {', '.join(data['team']['founders'])}. "
            if data['team'].get('team_members'):
                team_text += f"Team members: {', '.join(data['team']['team_members'])}"
            
            if team_text:
                company_doc.team = Section(
                    text=team_text,
                    bullets=data['team'].get('founders', []),
                    citations=citations
                )
        
        # Map product data
        if data.get('product'):
            product_text = ""
            if data['product'].get('description'):
                product_text += f"{data['product']['description']}. "
            if data['product'].get('problem_solved'):
                product_text += f"Problem solved: {data['product']['problem_solved']}"
            
            if product_text:
                company_doc.product = Section(
                    text=product_text,
                    bullets=data['product'].get('features', []),
                    citations=citations
                )
        
        # Map competitors data
        if data.get('competitors'):
            competitors_text = ""
            if data['competitors'].get('market_position'):
                competitors_text += f"Market position: {data['competitors']['market_position']}. "
            
            if competitors_text:
                company_doc.competitors = Section(
                    text=competitors_text,
                    bullets=data['competitors'].get('mentioned_competitors', []),
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
