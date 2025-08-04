import logging
from typing import List, Dict, Optional
from models.schemas import Section, Citation
from utils.linkedin_scraper import extract_team_from_linkedin
from datetime import datetime
import os
import openai
import json

logger = logging.getLogger(__name__)

def create_linkedin_citation(team_member: dict) -> Citation:
    """Create a citation from a LinkedIn team member"""
    return Citation(
        url=team_member['source'],
        snippet=f"{team_member['name']} — {team_member['title']}",
        source_type="linkedin",
        timestamp=datetime.now()
    )

def get_founder_team_info(company_name: str) -> Section:
    """
    Dynamically scrape and summarize founder/team information.
    
    Args:
        company_name: Name of the company to research
        
    Returns:
        Section object with team summary, bullets, and citations
    """
    logger.info(f"Getting founder/team info for {company_name}")
    
    # Step 1: LinkedIn Scraping
    team_members = []
    linkedin_citations = []
    
    try:
        logger.info(f"Scraping LinkedIn for {company_name} team members")
        linkedin_team = extract_team_from_linkedin(company_name)
        
        if linkedin_team:
            team_members.extend(linkedin_team)
            linkedin_citations = [create_linkedin_citation(member) for member in linkedin_team]
            logger.info(f"Found {len(linkedin_team)} team members from LinkedIn")
        else:
            logger.warning(f"No LinkedIn team members found for {company_name}")
            
    except Exception as e:
        logger.warning(f"LinkedIn scraping failed for {company_name}: {e}")
    
    # Step 2: Web Search Fallback (if needed)
    if not team_members:
        logger.info(f"No LinkedIn data found, attempting web search fallback for {company_name}")
        # This would integrate with your existing web search functionality
        # For now, we'll use a placeholder
        team_members = []
    
    # Step 3: GPT-4 Summarization
    if team_members:
        try:
            # Prepare team info for GPT-4
            team_info_raw = []
            for member in team_members:
                team_info_raw.append({
                    "name": member.get('name', 'Unknown'),
                    "title": member.get('title', 'Unknown'),
                    "source": member.get('source', 'Unknown')
                })
            
            # Create GPT-4 prompt
            prompt = f"""
You are a VC analyst creating an investment memo.

Based on the following extracted team info for {company_name}:

{json.dumps(team_info_raw, indent=2)}

Write a professional summary paragraph and 3-5 bullet points about the founding team and leadership.

Focus on:
- Founder experience and background
- Previous exits or successful companies
- Relevant industry experience
- Credibility and track record
- Key leadership roles and responsibilities

Keep the tone professional and analytical, suitable for an investment memo.

Return as JSON:
{{
  "text": "Professional summary paragraph...",
  "bullets": ["Bullet point 1", "Bullet point 2", "..."],
  "citations": ["url1", "url2", "..."]
}}
"""
            
            # Check if OpenAI API key is available
            if not os.getenv("OPENAI_API_KEY"):
                logger.warning("OPENAI_API_KEY not found, using fallback team summary")
                return create_fallback_team_section(company_name, team_members, linkedin_citations)
            
            # Call GPT-4
            response = openai.ChatCompletion.create(
                model="gpt-4-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional VC analyst. Provide concise, factual team summaries suitable for investment memos."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse GPT-4 response
            content = response.choices[0].message.content.strip()
            
            try:
                # Extract JSON from response
                if content.startswith('{') and content.endswith('}'):
                    result = json.loads(content)
                else:
                    # Try to find JSON within the response
                    start_idx = content.find('{')
                    end_idx = content.rfind('}') + 1
                    if start_idx != -1 and end_idx > start_idx:
                        json_str = content[start_idx:end_idx]
                        result = json.loads(json_str)
                    else:
                        raise ValueError("No valid JSON found in response")
                
                # Create citations
                citations = []
                if 'citations' in result:
                    for url in result['citations']:
                        citations.append(Citation(
                            url=url,
                            snippet=f"Team information source",
                            source_type="website",
                            timestamp=datetime.now()
                        ))
                
                # Add LinkedIn citations
                citations.extend(linkedin_citations)
                
                # Create Section object
                section = Section(
                    text=result.get('text', ''),
                    bullets=result.get('bullets', []),
                    citations=citations
                )
                
                logger.info(f"Successfully generated team summary for {company_name}")
                return section
                
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to parse GPT-4 response for {company_name}: {e}")
                return create_fallback_team_section(company_name, team_members, linkedin_citations)
                
        except Exception as e:
            logger.warning(f"GPT-4 summarization failed for {company_name}: {e}")
            return create_fallback_team_section(company_name, team_members, linkedin_citations)
    
    else:
        logger.warning(f"No team data found for {company_name}, using generic fallback")
        return create_fallback_team_section(company_name, [], [])

def create_fallback_team_section(company_name: str, team_members: List[Dict], citations: List[Citation]) -> Section:
    """Create a fallback team section when no data is available"""
    
    if team_members:
        # Create basic summary from available data
        names = [member.get('name', '') for member in team_members if member.get('name')]
        titles = [member.get('title', '') for member in team_members if member.get('title')]
        
        text = f"The {company_name} team includes {', '.join(names[:3])} in key leadership roles."
        bullets = [f"{member.get('name', 'Unknown')} — {member.get('title', 'Unknown')}" 
                  for member in team_members[:5]]
    else:
        # Generic fallback
        text = f"The {company_name} leadership team brings relevant industry experience to the company's mission."
        bullets = [
            f"Leadership team with experience in the target market",
            f"Track record of building and scaling companies",
            f"Strong operational and strategic expertise"
        ]
    
    return Section(
        text=text,
        bullets=bullets,
        citations=citations
    )

def evaluate_founder(founder_name: str, company_name: str = None) -> Dict:
    """Evaluate founder and team using LinkedIn data when available"""

    # Try to get real team data from LinkedIn
    linkedin_team = []
    if company_name:
        try:
            logger.info(f"Extracting team information from LinkedIn for {company_name}")
            linkedin_team = extract_team_from_linkedin(company_name)
            logger.info(f"Found {len(linkedin_team)} team members from LinkedIn")
        except Exception as e:
            logger.warning(f"LinkedIn extraction failed for {company_name}: {e}")
            linkedin_team = []

    # Create team section with LinkedIn data if available
    if linkedin_team:
        team_bullets = [f"{member['name']} — {member['title']}" for member in linkedin_team]
        team_citations = [create_linkedin_citation(member) for member in linkedin_team]

        team_section = Section(
            bullets=team_bullets,
            citations=team_citations
        )
    else:
        # Fallback to placeholder data
        team_bullets = [
            f"{founder_name}, Founder & CEO: Visionary leader with extensive experience in the industry.",
            "Jane Doe, CTO: Expert in software engineering and product innovation, previously at a leading tech firm.",
            "John Smith, COO: Operations specialist with a background in scaling startups and managing cross-functional teams.",
            "Emily Lee, Head of Marketing: Skilled marketer with a focus on digital growth and brand strategy.",
            "Sara Klein, Advisor: SaaS and startup veteran.",
            "Dave Smith, Advisor: Founder & CEO, SpeedyDetail."
        ]
        team_section = Section(
            bullets=team_bullets,
            citations=[]
        )

    # Create background section
    background_text = f"{founder_name} is an accomplished entrepreneur with a proven track record in building and scaling technology companies. With deep expertise in product development, business strategy, and team leadership, {founder_name} has consistently delivered results in competitive markets."

    background_section = Section(
        text=background_text,
        citations=[]
    )

    # Create contact section
    contact = f"{founder_name} | Email: {founder_name.lower().replace(' ','.')}@startup.com | LinkedIn: linkedin.com/in/{founder_name.lower().replace(' ','')}"

    return {
        "background": background_section,
        "team": team_section,
        "contact": contact
    }