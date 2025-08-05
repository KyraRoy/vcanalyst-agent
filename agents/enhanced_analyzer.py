import os
import logging
import openai
import json
import requests
from typing import Dict, List, Optional
from datetime import datetime
from models.schemas import Section, Citation, StructuredCompanyDoc
from utils.google_search import search_google
from utils.web_scraper import WebScraper

logger = logging.getLogger(__name__)

class EnhancedAnalyzer:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.scraper = WebScraper()
    
    def analyze_pitch_deck_with_gpt(self, slides_data: List[Dict], company_name: str) -> Dict[str, Section]:
        """
        Analyze pitch deck slides using GPT-4 for intelligent content extraction.
        
        Args:
            slides_data: List of slide data with text content
            company_name: Name of the company
            
        Returns:
            Dictionary of structured sections
        """
        logger.info(f"Starting GPT-4 analysis for {company_name}")
        
        # Prepare comprehensive prompt for GPT-4
        prompt = self._create_comprehensive_prompt(slides_data, company_name)
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a professional VC analyst with expertise in investment memo creation. 
                        Your task is to extract and structure information from pitch deck slides into a comprehensive investment memo format.
                        
                        Focus on:
                        - Accurate problem/solution identification
                        - Market size and opportunity analysis
                        - Team background and credibility
                        - Traction and financial metrics
                        - Competitive landscape
                        - Business model and revenue streams
                        - Growth strategy and go-to-market
                        - Risk factors and defensibility
                        
                        Be precise, professional, and analytical in your assessment."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse the structured response
            sections = self._parse_gpt_response(content, company_name)
            
            logger.info(f"Successfully analyzed {len(sections)} sections with GPT-4")
            return sections
            
        except Exception as e:
            logger.error(f"GPT-4 analysis failed: {e}")
            return {}
    
    def _create_comprehensive_prompt(self, slides_data: List[Dict], company_name: str) -> str:
        """Create a comprehensive prompt for GPT-4 analysis"""
        
        # Combine all slide content
        all_content = []
        for i, slide in enumerate(slides_data, 1):
            slide_text = slide.get('text', '').strip()
            if slide_text:
                all_content.append(f"Slide {i}:\n{slide_text}\n")
        
        combined_content = "\n".join(all_content)
        
        prompt = f"""
               You are a professional VC research analyst conducting comprehensive due diligence on {company_name}. 
               Your task is to research and analyze this company using publicly available sources to create a detailed investment memo.
               
               RESEARCH CONTEXT:
               {combined_content}
               
               For each section below, provide the actual answer to the specific question, not the question itself.
               Do NOT use generic templates or placeholder text. Get actual insights and facts.
               
               Return the analysis as a JSON object with this structure:
               {{
                   "executive_summary": {{
                       "text": "Provide a comprehensive overview of {company_name} including their mission, current status, and funding history. Answer in 150+ words with specific details.",
                       "bullets": ["List the 5 most important facts about {company_name} that investors should know with specific details."]
                   }},
                   "company_overview": {{
                       "text": "Describe the founding story and history of {company_name} including founding year, founders, headquarters, and key milestones. Answer in 150+ words with specific dates and facts.",
                       "bullets": ["List 5 key milestones and achievements in {company_name} history with specific dates."]
                   }},
                   "problem": {{
                       "text": "Describe the specific problem that {company_name} solves, who are the people or businesses affected, and the pain points and market gaps. Answer in 150+ words with concrete examples.",
                       "bullets": ["List the 5 biggest pain points that {company_name} addresses with specific details about the problems."]
                   }},
                   "solution": {{
                       "text": "Explain how {company_name} solves the problem, their unique approach and value proposition. Describe their solution in detail. Answer in 150+ words with specific features and benefits.",
                       "bullets": ["List the 5 key features or benefits of {company_name} solution with specific details about what makes them unique."]
                   }},
                   "product": {{
                       "text": "Describe {company_name} product or service, how it works, the technology, features, and user experience. Answer in 150+ words with technical details.",
                       "bullets": ["List the 5 most important features of {company_name} product with specific functionality details."]
                   }},
                   "business_model": {{
                       "text": "Explain how {company_name} makes money, their revenue model, pricing strategy, and monetization approach. Answer in 150+ words with specific numbers and strategies.",
                       "bullets": ["List the 5 key revenue streams or pricing strategies for {company_name} with specific details."]
                   }},
                   "market_size": {{
                       "text": "Describe the market size and opportunity for {company_name} including TAM, SAM, SOM data, growth rates, and market trends. Answer in 150+ words with specific numbers.",
                       "bullets": ["List the 5 key market insights for {company_name} industry with specific market data and trends."]
                   }},
                   "traction": {{
                       "text": "Describe {company_name} current traction and growth metrics including user numbers, revenue, partnerships, and expansion data. Answer in 150+ words with specific numbers.",
                       "bullets": ["List the 5 most impressive traction metrics for {company_name} with specific numbers and growth rates."]
                   }},
                   "growth_strategy": {{
                       "text": "Describe {company_name} growth strategy and go-to-market approach, how they acquire customers and expand. Answer in 150+ words with specific tactics.",
                       "bullets": ["List the 5 key growth strategies for {company_name} with specific customer acquisition tactics."]
                   }},
                   "team": {{
                       "text": "Describe the key team members and founders of {company_name}, their backgrounds and prior successes. Answer in 150+ words with specific details about leadership.",
                       "bullets": ["List the 5 most important team members at {company_name} with their roles and backgrounds."]
                   }},
                   "competitors": {{
                       "text": "Describe {company_name} main competitors, how they differentiate themselves, and the competitive landscape. Answer in 150+ words with specific company names.",
                       "bullets": ["List the 5 main competitors of {company_name} with how they differentiate."]
                   }},
                   "financials": {{
                       "text": "Describe {company_name} financials and funding history including revenue, funding raised, valuation, and financial metrics. Answer in 150+ words with specific numbers.",
                       "bullets": ["List the 5 key financial metrics for {company_name} with specific numbers and funding details."]
                   }},
                   "risks": {{
                       "text": "Describe the main risks and challenges facing {company_name} including execution, regulatory, market, and competitive risks. Answer in 150+ words with specific risk factors.",
                       "bullets": ["List the 5 biggest risks for {company_name} with specific risk factors and challenges."]
                   }},
                   "timing": {{
                       "text": "Explain why now is the right time for {company_name}, what market conditions and trends make this opportunity timely. Answer in 150+ words with specific timing factors.",
                       "bullets": ["List the 5 key timing factors that make {company_name} opportunity relevant now with specific market conditions."]
                   }},
                   "moat": {{
                       "text": "Describe {company_name} competitive moat and defensibility, how they protect their market position. Answer in 150+ words with specific defensibility factors.",
                       "bullets": ["List the 5 key defensibility factors for {company_name} with specific competitive advantages."]
                   }}
               }}
               
               Important guidelines:
               - Provide actual answers to each question, not the questions themselves
               - Do NOT use generic templates or placeholder text
               - Get actual facts, numbers, and specific details
               - Use real company names, founder names, and specific metrics
               - Focus on meaningful business insights with detailed analysis
               - If information is limited, provide reasonable industry-based insights
               - Include recent news, funding announcements, and current market positioning
               - Provide detailed bullet points with substantial insights, not generic statements
               """
        
        return prompt
    
    def _parse_gpt_response(self, content: str, company_name: str) -> Dict[str, Section]:
        """Parse GPT-4 response into structured sections"""
        try:
            # Try to extract JSON from response
            if content.startswith('{') and content.endswith('}'):
                data = json.loads(content)
            else:
                # Try to find JSON within the response
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                if start_idx != -1 and end_idx > start_idx:
                    json_str = content[start_idx:end_idx]
                    data = json.loads(json_str)
                else:
                    raise ValueError("No valid JSON found in response")
            
            # Convert to Section objects
            sections = {}
            for section_name, section_data in data.items():
                if isinstance(section_data, dict):
                    section = Section(
                        text=section_data.get('text', ''),
                        bullets=section_data.get('bullets', []),
                        citations=[Citation(
                            url="https://web_research.com",
                            snippet=f"Web research data for {company_name}",
                            source_type="web_research",
                            timestamp=datetime.now()
                        )]
                    )
                    sections[section_name] = section
            
            return sections
            
        except Exception as e:
            logger.error(f"Failed to parse GPT response: {e}")
            return {}
    
    def enhance_with_web_research(self, company_name: str, industry: str = None) -> Dict[str, Section]:
        """
        Enhance analysis with web research including McKinsey reports and industry data.
        
        Args:
            company_name: Name of the company
            industry: Industry sector (optional)
            
        Returns:
            Dictionary of additional research sections
        """
        logger.info(f"Enhancing analysis with web research for {company_name}")
        
        # Search queries for additional research
        search_queries = [
            f"{company_name} company overview",
            f"{company_name} funding news",
            f"{company_name} team founders",
            f"{company_name} revenue growth",
            f"{company_name} competitors",
            f"{company_name} market share"
        ]
        
        if industry:
            search_queries.extend([
                f"{industry} market size 2024",
                f"{industry} growth trends",
                f"McKinsey {industry} report",
                f"{industry} TAM SAM SOM"
            ])
        
        # Perform web searches
        research_data = {}
        for query in search_queries:
            try:
                results = search_google(company_name, [query])
                if results:
                    research_data[query] = results
            except Exception as e:
                logger.warning(f"Web search failed for query '{query}': {e}")
        
        # Use GPT-4 to analyze research data
        if research_data:
            return self._analyze_research_with_gpt(research_data, company_name)
        
        return {}
    
    def _analyze_research_with_gpt(self, research_data: Dict, company_name: str) -> Dict[str, Section]:
        """Use GPT-4 to analyze web research data"""
        
        # Prepare research data for GPT analysis
        research_text = ""
        for query, results in research_data.items():
            research_text += f"\nQuery: {query}\n"
            for result in results[:2]:  # Top 2 results per query
                research_text += f"Source: {result.get('url', 'Unknown')}\n"
                research_text += f"Content: {result.get('text', '')[:500]}...\n\n"
        
        prompt = f"""
        Analyze the following web research data for {company_name} and extract relevant insights for an investment memo.
        
        RESEARCH DATA:
        {research_text}
        
        Please provide insights on:
        1. Market validation and trends
        2. Competitive landscape updates
        3. Team credibility and background
        4. Recent funding or traction news
        5. Industry-specific insights
        
        Return as JSON with sections for market_validation, competitive_landscape, team_credibility, recent_news, industry_insights.
        """
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional VC analyst. Extract relevant insights from web research data."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            return self._parse_gpt_response(content, company_name)
            
        except Exception as e:
            logger.error(f"Research analysis failed: {e}")
            return {}
    
    def create_comprehensive_memo(self, pitch_deck_sections: Dict[str, Section], 
                                research_sections: Dict[str, Section], 
                                company_name: str) -> StructuredCompanyDoc:
        """
        Create a comprehensive investment memo combining pitch deck and research data.
        
        Args:
            pitch_deck_sections: Sections extracted from pitch deck
            research_sections: Sections from web research
            company_name: Name of the company
            
        Returns:
            StructuredCompanyDoc with comprehensive analysis
        """
        # Create base company document
        company_doc = StructuredCompanyDoc(name=company_name)
        
        # Map pitch deck sections to company document
        section_mapping = {
            'executive_summary': 'intro',
            'company_overview': 'intro',
            'problem': 'problem',
            'solution': 'solution',
            'product': 'product',
            'business_model': 'business_model',
            'market_size': 'market',
            'traction': 'traction',
            'growth_strategy': 'growth_strategy',
            'team': 'team',
            'competitors': 'competitors',
            'financials': 'financials',
            'risks': 'risks',
            'timing': 'timing',
            'moat': 'moat'
        }
        
        # Apply pitch deck sections
        for gpt_section, doc_section in section_mapping.items():
            if gpt_section in pitch_deck_sections:
                setattr(company_doc, doc_section, pitch_deck_sections[gpt_section])
        
        # Enhance with research sections
        for section_name, section_data in research_sections.items():
            if hasattr(company_doc, section_name):
                setattr(company_doc, section_name, section_data)
        
        return company_doc 

    def generate_memo_from_web_research(self, company_name: str, industry: str = None) -> StructuredCompanyDoc:
        """
        Generate a comprehensive investment memo from web research only.
        
        Args:
            company_name: Name of the company
            industry: Industry sector (optional)
            
        Returns:
            StructuredCompanyDoc with complete memo
        """
        logger.info(f"Starting web research memo generation for {company_name}")
        
        try:
            # Add timeout wrapper to prevent infinite hanging
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Analysis timed out for {company_name}")
            
            # Set 3-minute timeout
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(180)  # 3 minutes
            
            try:
                # Perform comprehensive web research
                research_data = self._comprehensive_web_research(company_name, industry)
                
                if not research_data:
                    logger.warning(f"No web research data found for {company_name}, falling back to GPT knowledge")
                    # Fallback to GPT knowledge
                    memo_sections = self._generate_memo_from_gpt_knowledge(company_name, industry)
                else:
                    # Synthesize research into memo sections
                    memo_sections = self._synthesize_research_to_memo(research_data, company_name)
                
                # Create comprehensive memo
                memo = self._create_comprehensive_memo_from_research(memo_sections, company_name)
                
                signal.alarm(0)  # Cancel timeout
                logger.info(f"Successfully generated memo for {company_name}")
                return memo
                
            except TimeoutError as e:
                logger.error(f"Analysis timed out for {company_name}: {e}")
                # Fallback to GPT knowledge
                memo_sections = self._generate_memo_from_gpt_knowledge(company_name, industry)
                memo = self._create_comprehensive_memo_from_research(memo_sections, company_name)
                return memo
                
            except Exception as e:
                logger.error(f"Web research failed for {company_name}: {e}")
                # Fallback to GPT knowledge
                memo_sections = self._generate_memo_from_gpt_knowledge(company_name, industry)
                memo = self._create_comprehensive_memo_from_research(memo_sections, company_name)
                return memo
                
        except Exception as e:
            logger.error(f"Unexpected error in memo generation for {company_name}: {e}")
            # Final fallback
            memo_sections = self._generate_memo_from_gpt_knowledge(company_name, industry)
            memo = self._create_comprehensive_memo_from_research(memo_sections, company_name)
            return memo
    
    def _comprehensive_web_research(self, company_name: str, industry: str = None) -> Dict:
        """
        Perform comprehensive web research for a company.
        
        Args:
            company_name: Name of the company
            industry: Industry sector (optional)
            
        Returns:
            Dictionary of research data
        """
        logger.info(f"Starting web research for {company_name}")
        
        # Define comprehensive search queries (LIMITED to prevent hanging)
        search_queries = [
            # Company overview (most important)
            f"{company_name} company overview",
            f"{company_name} about us",
            
            # Problem and solution
            f"{company_name} problem solution",
            f"{company_name} what problem does it solve",
            
            # Business model
            f"{company_name} business model",
            f"{company_name} revenue model",
            
            # Market and opportunity
            f"{company_name} market size",
            f"{industry} market size 2024" if industry else f"{company_name} industry market size",
            
            # Traction and metrics
            f"{company_name} revenue growth",
            f"{company_name} funding raised",
            
            # Team and founders
            f"{company_name} founders team",
            f"{company_name} CEO CTO",
            
            # Competition
            f"{company_name} competitors",
            f"{company_name} competitive landscape",
            
            # Financials
            f"{company_name} financials",
            f"{company_name} funding rounds",
            
            # Growth strategy
            f"{company_name} growth strategy",
            f"{company_name} expansion plans",
            
            # Industry insights
            f"{industry} trends 2024" if industry else f"{company_name} industry trends",
            f"McKinsey {industry} report" if industry else f"McKinsey {company_name} industry report"
        ]
        
        # LIMIT to 10 queries to prevent hanging
        limited_queries = search_queries[:10]
        logger.info(f"Processing {len(limited_queries)} search queries for {company_name}")
        
        # Perform web searches with timeout
        research_data = {}
        for i, query in enumerate(limited_queries):
            try:
                logger.info(f"Searching query {i+1}/{len(limited_queries)}: {query}")
                results = search_google(company_name, [query])
                if results:
                    research_data[query] = results
                    logger.info(f"Found {len(results)} results for query: {query}")
                else:
                    logger.warning(f"No results found for query: {query}")
            except Exception as e:
                logger.warning(f"Web search failed for query '{query}': {e}")
        
        logger.info(f"Completed web research for {company_name}: {len(research_data)} successful queries")
        return research_data
    
    def _synthesize_research_to_memo(self, research_data: Dict, company_name: str) -> Dict[str, Section]:
        """
        Use GPT-4 to synthesize web research into structured memo sections.
        
        Args:
            research_data: Dictionary of web research data
            company_name: Name of the company
            
        Returns:
            Dictionary of structured memo sections
        """
        logger.info(f"Synthesizing research into memo for {company_name}")
        
        # Prepare research data for GPT analysis and track sources
        research_text = ""
        source_urls = []  # Track all source URLs
        
        for query, results in research_data.items():
            research_text += f"\nQuery: {query}\n"
            for result in results[:3]:  # Top 3 results per query
                url = result.get('url', 'Unknown')
                source_urls.append(url)  # Track the URL
                research_text += f"Source: {url}\n"
                research_text += f"Content: {result.get('text', '')[:500]}...\n\n"
        
        prompt = f"""
               You are a professional VC research analyst conducting comprehensive due diligence on {company_name}. 
               Your task is to research and analyze this company using publicly available sources to create a detailed investment memo.
               
               RESEARCH DATA:
               {research_text}
               
               For each section below, provide the actual answer to the specific question, not the question itself.
               Do NOT use generic templates or placeholder text. Get actual insights and facts.
               
               If information is not available in the research, provide reasonable industry-based insights.
               
               Return as JSON with these sections:
               {{
                   "recommendations": {{
                       "text": "Provide a comprehensive investment recommendation for {company_name} based on the 4 key parameters: Speed (10x faster execution), Depth (domain expertise), Taste (intuition and decision quality), and Influence (attention and positioning). Be brutally honest about whether we should invest and why. Answer in 200+ words with specific reasoning.",
                       "bullets": [
                           "Should we invest? [Yes/No] with reasoning on Speed, Depth, Taste, Influence",
                           "Key questions to ask founders to validate investment thesis",
                           "Red flags and risks to watch out for (be brutally honest)",
                           "SWOT analysis of investing in this company"
                       ]
                   }},
                   "executive_summary": {{
                       "text": "Provide a comprehensive overview of {company_name} including their mission, current status, and funding history. Answer in 150+ words with specific details.",
                       "bullets": ["List the 5 most important facts about {company_name} that investors should know with specific details."]
                   }},
                   "company_overview": {{
                       "text": "Describe the founding story and history of {company_name} including founding year, founders, headquarters, and key milestones. Answer in 150+ words with specific dates and facts.",
                       "bullets": ["List 5 key milestones and achievements in {company_name} history with specific dates."]
                   }},
                   "problem": {{
                       "text": "Describe the specific problem that {company_name} solves, who are the people or businesses affected, and the pain points and market gaps. Answer in 150+ words with concrete examples.",
                       "bullets": ["List the 5 biggest pain points that {company_name} addresses with specific details about the problems."]
                   }},
                   "solution": {{
                       "text": "Explain how {company_name} solves the problem, their unique approach and value proposition. Describe their solution in detail. Answer in 150+ words with specific features and benefits.",
                       "bullets": ["List the 5 key features or benefits of {company_name} solution with specific details about what makes them unique."]
                   }},
                   "product": {{
                       "text": "Describe {company_name} product or service, how it works, the technology, features, and user experience. Answer in 150+ words with technical details.",
                       "bullets": ["List the 5 most important features of {company_name} product with specific functionality details."]
                   }},
                   "business_model": {{
                       "text": "Explain how {company_name} makes money, their revenue model, pricing strategy, and monetization approach. Answer in 150+ words with specific numbers and strategies.",
                       "bullets": ["List the 5 key revenue streams or pricing strategies for {company_name} with specific details."]
                   }},
                   "market_size": {{
                       "text": "Describe the market size and opportunity for {company_name} including TAM, SAM, SOM data, growth rates, and market trends. Answer in 150+ words with specific numbers.",
                       "bullets": ["List the 5 key market insights for {company_name} industry with specific market data and trends."]
                   }},
                   "traction": {{
                       "text": "Describe {company_name} current traction and growth metrics including user numbers, revenue, partnerships, and expansion data. Answer in 150+ words with specific numbers.",
                       "bullets": ["List the 5 most impressive traction metrics for {company_name} with specific numbers and growth rates."]
                   }},
                   "growth_strategy": {{
                       "text": "Describe {company_name} growth strategy and go-to-market approach, how they acquire customers and expand. Answer in 150+ words with specific tactics.",
                       "bullets": ["List the 5 key growth strategies for {company_name} with specific customer acquisition tactics."]
                   }},
                   "team": {{
                       "text": "Describe the key team members and founders of {company_name}, their backgrounds and prior successes. Answer in 150+ words with specific details about leadership.",
                       "bullets": ["List the 5 most important team members at {company_name} with their roles and backgrounds."]
                   }},
                   "competitors": {{
                       "text": "Describe {company_name} main competitors, how they differentiate themselves, and the competitive landscape. Answer in 150+ words with specific company names.",
                       "bullets": ["List the 5 main competitors of {company_name} with how they differentiate."]
                   }},
                   "financials": {{
                       "text": "Describe {company_name} financials and funding history including revenue, funding raised, valuation, and financial metrics. Answer in 150+ words with specific numbers.",
                       "bullets": ["List the 5 key financial metrics for {company_name} with specific numbers and funding details."]
                   }},
                   "risks": {{
                       "text": "Describe the key risks and challenges facing {company_name} including market risks, competitive risks, execution risks, and regulatory risks. Answer in 150+ words with specific concerns.",
                       "bullets": ["List the 5 biggest risks for {company_name} with specific details about potential challenges."]
                   }},
                   "timing": {{
                       "text": "Describe why now is the right time to invest in {company_name} including market timing, technology readiness, and competitive advantages. Answer in 150+ words with specific timing factors.",
                       "bullets": ["List the 5 key timing factors for investing in {company_name} with specific market and technology trends."]
                   }},
                   "moat": {{
                       "text": "Describe {company_name} competitive moat and defensibility including network effects, switching costs, brand, and technology advantages. Answer in 150+ words with specific moat characteristics.",
                       "bullets": ["List the 5 key competitive advantages for {company_name} with specific moat characteristics."]
                   }}
               }}
               
               Important guidelines:
               - Provide actual answers to each question, not the questions themselves
               - Do NOT use generic templates or placeholder text
               - Get actual facts, numbers, and specific details
               - Use real company names, founder names, and specific metrics
               - Focus on meaningful business insights with detailed analysis
               - If information is limited, provide reasonable industry-based insights
               - Include recent news, funding announcements, and current market positioning
               - Provide detailed bullet points with substantial insights, not generic statements
               """
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a professional VC analyst with expertise in investment memo creation. 
                        Your task is to synthesize web research into structured investment memo sections.
                        
                        Focus on:
                        - Accurate problem/solution identification
                        - Market size and opportunity analysis
                        - Team background and credibility
                        - Traction and financial metrics
                        - Competitive landscape
                        - Business model and revenue streams
                        - Growth strategy and go-to-market
                        - Risk factors and defensibility
                        
                        Be precise, professional, and analytical in your assessment."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse the structured response
            sections = self._parse_gpt_response(content, company_name)
            
            # Add real citations to each section
            for section_name, section in sections.items():
                if section and hasattr(section, 'citations'):
                    # Create citations from actual source URLs
                    for url in source_urls:
                        if url and url != 'Unknown':
                            # Determine source type based on URL
                            source_type = self._determine_source_type(url)
                            citation = Citation(
                                source_type=source_type,
                                url=url,
                                title=f"Source: {source_type}",
                                timestamp=datetime.now()
                            )
                            section.citations.append(citation)
            
            logger.info(f"Successfully synthesized {len(sections)} sections with real citations")
            return sections
            
        except Exception as e:
            logger.error(f"Research synthesis failed: {e}")
            return {}
    
    def _determine_source_type(self, url: str) -> str:
        """Determine the source type based on URL"""
        url_lower = url.lower()
        
        if 'linkedin.com' in url_lower:
            return 'LinkedIn'
        elif 'crunchbase.com' in url_lower:
            return 'Crunchbase'
        elif 'mckinsey.com' in url_lower:
            return 'McKinsey Report'
        elif 'techcrunch.com' in url_lower:
            return 'TechCrunch'
        elif 'forbes.com' in url_lower:
            return 'Forbes'
        elif 'bloomberg.com' in url_lower:
            return 'Bloomberg'
        elif 'wsj.com' in url_lower or 'wallstreetjournal.com' in url_lower:
            return 'Wall Street Journal'
        elif 'reuters.com' in url_lower:
            return 'Reuters'
        elif 'cnbc.com' in url_lower:
            return 'CNBC'
        elif 'venturebeat.com' in url_lower:
            return 'VentureBeat'
        elif 'pitchbook.com' in url_lower:
            return 'PitchBook'
        elif 'statista.com' in url_lower:
            return 'Statista'
        elif 'gartner.com' in url_lower:
            return 'Gartner'
        elif 'idc.com' in url_lower:
            return 'IDC'
        elif 'bain.com' in url_lower:
            return 'Bain & Company'
        elif 'bcg.com' in url_lower:
            return 'Boston Consulting Group'
        elif 'deloitte.com' in url_lower:
            return 'Deloitte'
        elif 'pwc.com' in url_lower:
            return 'PwC'
        elif 'ey.com' in url_lower:
            return 'EY'
        elif 'kpmg.com' in url_lower:
            return 'KPMG'
        elif 'google.com' in url_lower:
            return 'Google Search'
        elif 'youtube.com' in url_lower:
            return 'YouTube'
        elif 'twitter.com' in url_lower or 'x.com' in url_lower:
            return 'Twitter/X'
        elif 'facebook.com' in url_lower:
            return 'Facebook'
        elif 'instagram.com' in url_lower:
            return 'Instagram'
        elif 'medium.com' in url_lower:
            return 'Medium'
        elif 'substack.com' in url_lower:
            return 'Substack'
        elif 'github.com' in url_lower:
            return 'GitHub'
        elif 'stackoverflow.com' in url_lower:
            return 'Stack Overflow'
        elif 'reddit.com' in url_lower:
            return 'Reddit'
        elif 'quora.com' in url_lower:
            return 'Quora'
        elif 'wikipedia.org' in url_lower:
            return 'Wikipedia'
        elif 'news.ycombinator.com' in url_lower:
            return 'Hacker News'
        else:
            # Extract domain name for unknown sources
            from urllib.parse import urlparse
            try:
                domain = urlparse(url).netloc
                if domain:
                    return f"{domain.title()}"
                else:
                    return "Web Research"
            except:
                return "Web Research"
    
    def _create_comprehensive_memo_from_research(self, memo_sections: Dict[str, Section], company_name: str) -> StructuredCompanyDoc:
        """
        Create a comprehensive investment memo from research-based sections.
        
        Args:
            memo_sections: Dictionary of memo sections from research
            company_name: Name of the company
            
        Returns:
            StructuredCompanyDoc with comprehensive analysis
        """
        # Create base company document
        company_doc = StructuredCompanyDoc(name=company_name)
        
        # Map research sections to company document
        section_mapping = {
            'recommendations': 'recommendations',
            'executive_summary': 'intro',
            'company_overview': 'intro',
            'problem': 'problem',
            'solution': 'solution',
            'product': 'product',
            'business_model': 'business_model',
            'market_size': 'market',
            'traction': 'traction',
            'growth_strategy': 'growth_strategy',
            'team': 'team',
            'competitors': 'competitors',
            'financials': 'financials',
            'risks': 'risks',
            'timing': 'timing',
            'moat': 'moat'
        }
        
        # Apply research sections
        for research_section, doc_section in section_mapping.items():
            if research_section in memo_sections:
                setattr(company_doc, doc_section, memo_sections[research_section])
        
        return company_doc 

    def _generate_memo_from_gpt_knowledge(self, company_name: str, industry: str = None) -> Dict[str, Section]:
        """
        Generate memo sections using GPT's knowledge when web research is not available.
        
        Args:
            company_name: Name of the company
            industry: Industry sector (optional)
            
        Returns:
            Dictionary of memo sections
        """
        prompt = f"""
        You are a professional VC research analyst conducting comprehensive due diligence on {company_name}. 
        Your task is to research and analyze this company using your knowledge to create a detailed investment memo.
        
        For each section below, provide the actual answer to the specific question, not the question itself.
        Do NOT use generic templates or placeholder text. Get actual insights and facts.
        
        Return the analysis as a JSON object with this structure:
        {{
            "recommendations": {{
                "text": "Provide a comprehensive investment recommendation for {company_name} based on the 4 key parameters: Speed (10x faster execution), Depth (domain expertise), Taste (intuition and decision quality), and Influence (attention and positioning). Be brutally honest about whether we should invest and why. Answer in 200+ words with specific reasoning.",
                "bullets": [
                    "Should we invest? [Yes/No] with reasoning on Speed, Depth, Taste, Influence",
                    "Key questions to ask founders to validate investment thesis",
                    "Red flags and risks to watch out for (be brutally honest)",
                    "SWOT analysis of investing in this company"
                ]
            }},
            "executive_summary": {{
                "text": "Provide a comprehensive overview of {company_name} including their mission, current status, and funding history. Answer in 150+ words with specific details.",
                "bullets": ["List the 5 most important facts about {company_name} that investors should know with specific details."]
            }},
            "company_overview": {{
                "text": "Describe the founding story and history of {company_name} including founding year, founders, headquarters, and key milestones. Answer in 150+ words with specific dates and facts.",
                "bullets": ["List 5 key milestones and achievements in {company_name} history with specific dates."]
            }},
            "problem": {{
                "text": "Describe the specific problem that {company_name} solves, who are the people or businesses affected, and the pain points and market gaps. Answer in 150+ words with concrete examples.",
                "bullets": ["List the 5 biggest pain points that {company_name} addresses with specific details about the problems."]
            }},
            "solution": {{
                "text": "Explain how {company_name} solves the problem, their unique approach and value proposition. Describe their solution in detail. Answer in 150+ words with specific features and benefits.",
                "bullets": ["List the 5 key features or benefits of {company_name} solution with specific details about what makes them unique."]
            }},
            "product": {{
                "text": "Describe {company_name} product or service, how it works, the technology, features, and user experience. Answer in 150+ words with technical details.",
                "bullets": ["List the 5 most important features of {company_name} product with specific functionality details."]
            }},
            "business_model": {{
                "text": "Explain how {company_name} makes money, their revenue model, pricing strategy, and monetization approach. Answer in 150+ words with specific numbers and strategies.",
                "bullets": ["List the 5 key revenue streams or pricing strategies for {company_name} with specific details."]
            }},
            "market_size": {{
                "text": "Describe the market size and opportunity for {company_name} including TAM, SAM, SOM data, growth rates, and market trends. Answer in 150+ words with specific numbers.",
                "bullets": ["List the 5 key market insights for {company_name} industry with specific market data and trends."]
            }},
            "traction": {{
                "text": "Describe {company_name} current traction and growth metrics including user numbers, revenue, partnerships, and expansion data. Answer in 150+ words with specific numbers.",
                "bullets": ["List the 5 most impressive traction metrics for {company_name} with specific numbers and growth rates."]
            }},
            "growth_strategy": {{
                "text": "Describe {company_name} growth strategy and go-to-market approach, how they acquire customers and expand. Answer in 150+ words with specific tactics.",
                "bullets": ["List the 5 key growth strategies for {company_name} with specific customer acquisition tactics."]
            }},
            "team": {{
                "text": "Describe the key team members and founders of {company_name}, their backgrounds and prior successes. Answer in 150+ words with specific details about leadership.",
                "bullets": ["List the 5 most important team members at {company_name} with their roles and backgrounds."]
            }},
            "competitors": {{
                "text": "Describe {company_name} main competitors, how they differentiate themselves, and the competitive landscape. Answer in 150+ words with specific company names.",
                "bullets": ["List the 5 main competitors of {company_name} with how they differentiate."]
            }},
            "financials": {{
                "text": "Describe {company_name} financials and funding history including revenue, funding raised, valuation, and financial metrics. Answer in 150+ words with specific numbers.",
                "bullets": ["List the 5 key financial metrics for {company_name} with specific numbers and funding details."]
            }},
            "risks": {{
                "text": "Describe the main risks and challenges facing {company_name} including execution, regulatory, market, and competitive risks. Answer in 150+ words with specific risk factors.",
                "bullets": ["List the 5 biggest risks for {company_name} with specific risk factors and challenges."]
            }},
            "timing": {{
                "text": "Explain why now is the right time for {company_name}, what market conditions and trends make this opportunity timely. Answer in 150+ words with specific timing factors.",
                "bullets": ["List the 5 key timing factors that make {company_name} opportunity relevant now with specific market conditions."]
            }},
            "moat": {{
                "text": "Describe {company_name} competitive moat and defensibility, how they protect their market position. Answer in 150+ words with specific defensibility factors.",
                "bullets": ["List the 5 key defensibility factors for {company_name} with specific competitive advantages."]
            }}
        }}
        
        Important guidelines:
        - Provide actual answers to each question, not the questions themselves
        - Do NOT use generic templates or placeholder text
        - Get actual facts, numbers, and specific details
        - Use real company names, founder names, and specific metrics
        - Focus on meaningful business insights with detailed analysis
        - If information is limited, provide reasonable industry-based insights
        - Include recent news, funding announcements, and current market positioning
        - Provide detailed bullet points with substantial insights, not generic statements
        - For recommendations: Be brutally honest about investment potential based on Speed (10x execution), Depth (domain expertise), Taste (intuition), and Influence (attention/positioning)
        """
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            
            logger.info(f"Making OpenAI API call for {company_name}")
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional VC analyst. Create comprehensive investment memos using your knowledge of companies and industries."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            content = response.choices[0].message.content.strip()
            logger.info(f"OpenAI API call successful for {company_name}, response length: {len(content)}")
            
            result = self._parse_gpt_response(content, company_name)
            logger.info(f"Parsed GPT response for {company_name}, got {len(result)} sections")
            return result
            
        except Exception as e:
            logger.error(f"GPT knowledge generation failed for {company_name}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {} 