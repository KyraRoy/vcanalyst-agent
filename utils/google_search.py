import os
import time
import logging
import requests
from typing import List, Dict, Optional
from datetime import datetime
import trafilatura
from utils.web_scraper import TextCleaner

logger = logging.getLogger(__name__)

class GoogleSearcher:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('SERPAPI_KEY')
        if not self.api_key:
            raise ValueError("SERPAPI_KEY not found in environment variables")
        
        self.base_url = "https://serpapi.com/search"
        self.text_cleaner = TextCleaner()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def search_google(self, company_name: str, queries: List[str]) -> List[Dict]:
        """Perform Google searches for a company and extract content"""
        results = []
        
        # Limit to max 5 queries to prevent hanging
        limited_queries = queries[:5]
        logger.info(f"Processing {len(limited_queries)} queries for {company_name}")
        
        for i, query in enumerate(limited_queries):
            try:
                logger.info(f"Searching for: {query} ({i+1}/{len(limited_queries)})")
                
                # Perform search with timeout
                search_results = self._perform_search(query)
                
                if not search_results:
                    logger.warning(f"No search results found for query: {query}")
                    continue
                
                # Process top 2 results (reduced from 3)
                processed_count = 0
                for result in search_results[:2]:
                    try:
                        # Extract content from URL with timeout
                        content = self._extract_content(result['link'])
                        
                        if content and len(content) > 100:  # Only add if meaningful content
                            results.append({
                                "query": query,
                                "url": result['link'],
                                "title": result.get('title', ''),
                                "snippet": result.get('snippet', ''),
                                "text": content
                            })
                            processed_count += 1
                            
                            # Limit to 1 result per query to speed up
                            if processed_count >= 1:
                                break
                    
                    except Exception as e:
                        logger.warning(f"Failed to extract content from {result.get('link', '')}: {e}")
                
                # Rate limiting
                time.sleep(1.0)  # Reduced from 1.5
                
            except Exception as e:
                logger.error(f"Failed to search for '{query}': {e}")
        
        logger.info(f"Completed web search for {company_name}: {len(results)} results")
        return results
    
    def _perform_search(self, query: str, max_retries: int = 3) -> List[Dict]:
        """Perform a Google search with retry logic"""
        for attempt in range(max_retries):
            try:
                params = {
                    'q': query,
                    'api_key': self.api_key,
                    'engine': 'google',
                    'num': 3  # Get top 3 results
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
    
    def _extract_content(self, url: str, max_retries: int = 3) -> Optional[str]:
        """Extract cleaned content from a URL with retry logic"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                
                # Extract main content using trafilatura
                extracted_text = trafilatura.extract(response.text, include_comments=False, include_tables=False)
                
                if not extracted_text:
                    return None
                
                # Clean the extracted text
                cleaned_text = self.text_cleaner.clean_text(extracted_text)
                
                return cleaned_text if cleaned_text else None
                
            except Exception as e:
                logger.warning(f"Content extraction attempt {attempt + 1} failed for {url}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"All content extraction attempts failed for {url}")
                    return None

def search_google(company_name: str, queries: List[str]) -> List[Dict]:
    """Main function to search Google for company information"""
    try:
        searcher = GoogleSearcher()
        return searcher.search_google(company_name, queries)
    except Exception as e:
        logger.error(f"Google search failed: {e}")
        return [] 