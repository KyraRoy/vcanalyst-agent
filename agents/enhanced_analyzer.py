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
        
        openai.api_key = self.api_key
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
        Generate a comprehensive investment memo using only web research when no pitch deck is available.
        
        Args:
            company_name: Name of the company
            industry: Industry sector (optional)
            
        Returns:
            StructuredCompanyDoc with comprehensive analysis
        """
        logger.info(f"Generating memo from web research for {company_name}")
        
        # Comprehensive web research
        research_sections = self._comprehensive_web_research(company_name, industry)
        
        # If web research failed, generate content using GPT knowledge
        if not research_sections:
            logger.info(f"No web research data available for {company_name}, using GPT knowledge")
            memo_sections = self._generate_memo_from_gpt_knowledge(company_name, industry)
        else:
            # Use GPT-4 to synthesize the research into a structured memo
            memo_sections = self._synthesize_research_to_memo(research_sections, company_name)
        
        # Create comprehensive company document
        company_doc = self._create_comprehensive_memo_from_research(memo_sections, company_name)
        
        return company_doc
    
    def _comprehensive_web_research(self, company_name: str, industry: str = None) -> Dict:
        """
        Perform comprehensive web research for a company.
        
        Args:
            company_name: Name of the company
            industry: Industry sector (optional)
            
        Returns:
            Dictionary of research data
        """
        logger.info(f"Performing comprehensive web research for {company_name}")
        
        # Define comprehensive search queries
        search_queries = [
            # Company overview
            f"{company_name} company overview",
            f"{company_name} about us",
            f"{company_name} mission vision",
            
            # Problem and solution
            f"{company_name} problem solution",
            f"{company_name} what problem does it solve",
            f"{company_name} value proposition",
            
            # Product and features
            f"{company_name} product features",
            f"{company_name} platform technology",
            f"{company_name} how it works",
            
            # Business model
            f"{company_name} business model",
            f"{company_name} revenue model",
            f"{company_name} pricing",
            
            # Market and opportunity
            f"{company_name} market size",
            f"{company_name} TAM SAM SOM",
            f"{industry} market size 2024" if industry else f"{company_name} industry market size",
            
            # Traction and metrics
            f"{company_name} revenue growth",
            f"{company_name} user metrics",
            f"{company_name} funding raised",
            
            # Team and founders
            f"{company_name} founders team",
            f"{company_name} CEO CTO",
            f"{company_name} leadership",
            
            # Competition
            f"{company_name} competitors",
            f"{company_name} competitive landscape",
            f"{company_name} vs competitors",
            
            # Financials
            f"{company_name} financials",
            f"{company_name} funding rounds",
            f"{company_name} valuation",
            
            # Growth strategy
            f"{company_name} growth strategy",
            f"{company_name} expansion plans",
            f"{company_name} go-to-market",
            
            # Industry insights
            f"{industry} trends 2024" if industry else f"{company_name} industry trends",
            f"{industry} growth rate" if industry else f"{company_name} market growth",
            f"McKinsey {industry} report" if industry else f"McKinsey {company_name} industry report"
        ]
        
        # Perform web searches
        research_data = {}
        for query in search_queries:
            try:
                results = search_google(company_name, [query])
                if results:
                    research_data[query] = results
            except Exception as e:
                logger.warning(f"Web search failed for query '{query}': {e}")
        
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
        
        # Prepare research data for GPT analysis
        research_text = ""
        for query, results in research_data.items():
            research_text += f"\nQuery: {query}\n"
            for result in results[:3]:  # Top 3 results per query
                research_text += f"Source: {result.get('url', 'Unknown')}\n"
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
               
               Guidelines:
               - Provide actual answers to each question, not the questions themselves
               - Do NOT use generic templates or placeholder text
               - Get actual facts, numbers, and specific details
               - Use real company names, founder names, and specific metrics
               - Focus on meaningful business insights with detailed analysis
               - If information is limited, provide reasonable industry-based insights
               - Include recent news, funding announcements, and current market positioning
               - Provide detailed bullet points with substantial insights, not generic statements
               - For missing information, provide industry-standard insights or mark as "Limited information available"
               """
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional VC analyst. Create comprehensive investment memos from web research data."
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
            return self._parse_gpt_response(content, company_name)
            
        except Exception as e:
            logger.error(f"Research synthesis failed: {e}")
            return {}
    
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
            return self._parse_gpt_response(content, company_name)
            
        except Exception as e:
            logger.error(f"GPT knowledge generation failed: {e}")
            return {} 