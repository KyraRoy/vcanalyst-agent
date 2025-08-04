import os
import time
import logging
import re
import requests
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class LinkedInScraper:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('SERPAPI_KEY')
        if not self.api_key:
            raise ValueError("SERPAPI_KEY not found in environment variables")
        
        self.base_url = "https://serpapi.com/search"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def extract_team_from_linkedin(self, company_name: str) -> List[Dict[str, str]]:
        """Extract team members from LinkedIn using Google search"""
        try:
            logger.info(f"Searching LinkedIn for team members at {company_name}")
            
            # Perform LinkedIn search
            query = f"{company_name} site:linkedin.com/in"
            search_results = self._perform_search(query)
            
            team_members = []
            
            # Process top 5 results
            for result in search_results[:5]:
                try:
                    # Parse name and title from result title
                    parsed = self._parse_linkedin_title(result.get('title', ''))
                    
                    if parsed and self._is_valid_team_member(parsed):
                        team_members.append({
                            "name": parsed['name'],
                            "title": parsed['title'],
                            "source": result.get('link', '')
                        })
                
                except Exception as e:
                    logger.warning(f"Failed to parse LinkedIn result: {e}")
            
            logger.info(f"Found {len(team_members)} team members for {company_name}")
            return team_members
            
        except Exception as e:
            logger.error(f"LinkedIn search failed for {company_name}: {e}")
            return []
    
    def _perform_search(self, query: str, max_retries: int = 3) -> List[Dict]:
        """Perform a Google search with retry logic"""
        for attempt in range(max_retries):
            try:
                params = {
                    'q': query,
                    'api_key': self.api_key,
                    'engine': 'google',
                    'num': 5  # Get top 5 results
                }
                
                response = self.session.get(self.base_url, params=params, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                
                # Extract organic results
                organic_results = data.get('organic_results', [])
                return organic_results
                
            except Exception as e:
                logger.warning(f"Search attempt {attempt + 1} failed for '{query}': {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"All search attempts failed for '{query}'")
                    return []
    
    def _parse_linkedin_title(self, title: str) -> Optional[Dict[str, str]]:
        """Parse name and title from LinkedIn search result title"""
        if not title:
            return None
        
        # Common patterns for LinkedIn titles
        patterns = [
            # "Jane Doe - Co-founder & CEO at Company"
            r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*[-–]\s*(.+?)(?:\s+at\s+.+)?$',
            
            # "Jane Doe | Co-founder & CEO | Company"
            r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*\|\s*(.+?)(?:\s*\|\s*.+)?$',
            
            # "Jane Doe, Co-founder & CEO at Company"
            r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*(.+?)(?:\s+at\s+.+)?$',
            
            # "Co-founder & CEO at Company - Jane Doe"
            r'^(.+?)(?:\s+at\s+.+)?\s*[-–]\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)$',
        ]
        
        for pattern in patterns:
            match = re.match(pattern, title.strip())
            if match:
                groups = match.groups()
                if len(groups) >= 2:
                    # Determine which group is name vs title based on content
                    name, title_text = self._identify_name_and_title(groups[0], groups[1])
                    if name and title_text:
                        return {
                            "name": name.strip(),
                            "title": title_text.strip()
                        }
        
        return None
    
    def _identify_name_and_title(self, group1: str, group2: str) -> tuple:
        """Identify which group is the name vs title"""
        # Look for common title keywords
        title_keywords = [
            'founder', 'ceo', 'cto', 'coo', 'cfo', 'president', 'director', 'manager',
            'lead', 'head', 'chief', 'vp', 'vice president', 'co-founder', 'cofounder',
            'founder', 'partner', 'advisor', 'consultant', 'engineer', 'developer',
            'designer', 'marketing', 'sales', 'product', 'operations', 'finance'
        ]
        
        group1_lower = group1.lower()
        group2_lower = group2.lower()
        
        # Count title keywords in each group
        group1_score = sum(1 for keyword in title_keywords if keyword in group1_lower)
        group2_score = sum(1 for keyword in title_keywords if keyword in group2_lower)
        
        # If one group has significantly more title keywords, it's likely the title
        if group1_score > group2_score + 1:
            return group2, group1  # group2 is name, group1 is title
        elif group2_score > group1_score + 1:
            return group1, group2  # group1 is name, group2 is title
        else:
            # If scores are similar, assume first group is name (common pattern)
            return group1, group2
    
    def _is_valid_team_member(self, parsed: Dict[str, str]) -> bool:
        """Validate if the parsed result looks like a real team member"""
        name = parsed.get('name', '')
        title = parsed.get('title', '')
        
        # Basic validation
        if not name or not title:
            return False
        
        # Name should be 2+ words (first + last name)
        if len(name.split()) < 2:
            return False
        
        # Title should be reasonable length
        if len(title) < 3 or len(title) > 100:
            return False
        
        # Avoid obvious non-team results
        invalid_keywords = ['job', 'career', 'hiring', 'recruit', 'apply', 'position']
        if any(keyword in title.lower() for keyword in invalid_keywords):
            return False
        
        return True

def extract_team_from_linkedin(company_name: str) -> List[Dict[str, str]]:
    """Main function to extract team members from LinkedIn"""
    try:
        scraper = LinkedInScraper()
        return scraper.extract_team_from_linkedin(company_name)
    except Exception as e:
        logger.error(f"LinkedIn extraction failed: {e}")
        return [] 