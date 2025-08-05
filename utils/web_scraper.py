import requests
import time
import logging
import re
from typing import List, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import trafilatura
from models.schemas import RawDoc
from datetime import datetime
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TextCleaner:
    """Clean extracted text by removing UI noise and junk content"""
    
    def __init__(self):
        # Common junk phrases to filter out
        self.junk_phrases = [
            "accept cookies", "accept all cookies", "reject cookies", "cookie policy",
            "click here", "sign in", "login", "register", "subscribe", "newsletter",
            "scroll to top", "back to top", "menu", "navigation", "search",
            "⌘", "ctrl", "alt", "shift", "mousedown", "mouseup", "keydown",
            "play", "pause", "stop", "rewind", "fast forward", "volume",
            "zoom in", "zoom out", "fullscreen", "minimize", "maximize",
            "loading", "please wait", "processing", "submitting",
            "required field", "optional", "form", "submit", "reset",
            "privacy policy", "terms of service", "contact us", "about us",
            "follow us", "share", "like", "comment", "tweet",
            "download", "upload", "save", "delete", "edit", "copy",
            "close", "cancel", "ok", "yes", "no", "confirm",
            "error", "warning", "success", "info", "notice",
            "skip to content", "skip navigation", "accessibility",
            "font size", "high contrast", "screen reader"
        ]
        
        # UI control patterns
        self.ui_patterns = [
            r'\b[A-Z][a-z]+\s*[+\-]\s*[A-Z][a-z]*\b',  # Ctrl+A, Alt+F, etc.
            r'\b[A-Z][a-z]+\s*/\s*[A-Z][a-z]+\b',      # Ctrl/Alt, etc.
            r'\b\d+\s*[A-Z][a-z]+\b',                   # 1 Red, 2 Blue, etc.
            r'\b[A-Z][a-z]+\s*on/off\b',               # Red on/off
            r'\b[A-Z][a-z]+\s*[-–]\s*[A-Z][a-z]+\b',   # Up-down, left-right
            r'\b[A-Z][a-z]+\s*[+\-]\s*\d+\b',          # Zoom +/-, etc.
        ]
    
    def is_meaningful_text(self, text: str) -> bool:
        """Check if text contains meaningful content"""
        if not text or len(text.strip()) < 40:
            return False
        
        # Check for junk phrases
        text_lower = text.lower()
        junk_count = sum(1 for phrase in self.junk_phrases if phrase in text_lower)
        if junk_count > 0:
            return False
        
        # Check for UI patterns
        for pattern in self.ui_patterns:
            if re.search(pattern, text):
                return False
        
        # Must contain nouns or verbs (basic check)
        words = text.split()
        if len(words) < 3:
            return False
        
        # Check for common meaningful words
        meaningful_words = [
            'company', 'product', 'service', 'platform', 'solution', 'technology',
            'business', 'customer', 'user', 'market', 'industry', 'team',
            'revenue', 'growth', 'funding', 'investment', 'partnership',
            'launch', 'develop', 'create', 'build', 'provide', 'offer',
            'help', 'enable', 'power', 'drive', 'scale', 'expand'
        ]
        
        has_meaningful = any(word in text_lower for word in meaningful_words)
        return has_meaningful
    
    def clean_text(self, text: str) -> str:
        """Clean and filter text content"""
        if not text:
            return ""
        
        # Split into paragraphs
        paragraphs = text.split('\n\n')
        cleaned_paragraphs = []
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # Remove common UI noise
            lines = paragraph.split('\n')
            cleaned_lines = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Skip short lines that are likely UI controls
                if len(line) < 20 and not self.is_meaningful_text(line):
                    continue
                
                # Skip lines that are mostly junk
                if any(phrase in line.lower() for phrase in self.junk_phrases):
                    continue
                
                cleaned_lines.append(line)
            
            if cleaned_lines:
                cleaned_paragraph = '\n'.join(cleaned_lines)
                if self.is_meaningful_text(cleaned_paragraph):
                    cleaned_paragraphs.append(cleaned_paragraph)
        
        return '\n\n'.join(cleaned_paragraphs)

class WebScraper:
    def __init__(self, rate_limit_delay: float = 1.0, max_retries: int = 3):
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.text_cleaner = TextCleaner()
    
    def fetch_page(self, url: str) -> Optional[RawDoc]:
        """Fetch and extract content from a URL with retries"""
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Fetching {url} (attempt {attempt + 1})")
                
                # Use trafilatura.fetch_url with timeout instead of requests directly
                try:
                    downloaded = trafilatura.fetch_url(url, timeout=10)
                    if not downloaded:
                        logger.warning(f"Failed to download content from {url}")
                        return None
                    
                    # Extract main content using trafilatura
                    extracted_text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
                    
                    if not extracted_text:
                        # Fallback to BeautifulSoup for title
                        soup = BeautifulSoup(downloaded, 'html.parser')
                        title = soup.title.string if soup.title else url
                        extracted_text = soup.get_text(separator=' ', strip=True)
                    else:
                        # Get title from trafilatura or fallback
                        soup = BeautifulSoup(downloaded, 'html.parser')
                        title = soup.title.string if soup.title else url
                    
                except Exception as e:
                    logger.warning(f"trafilatura failed for {url}: {e}")
                    # Fallback to requests
                    response = self.session.get(url, timeout=10)
                    response.raise_for_status()
                    
                    # Extract main content using trafilatura
                    extracted_text = trafilatura.extract(response.text, include_comments=False, include_tables=False)
                    
                    if not extracted_text:
                        # Fallback to BeautifulSoup for title
                        soup = BeautifulSoup(response.text, 'html.parser')
                        title = soup.title.string if soup.title else url
                        extracted_text = soup.get_text(separator=' ', strip=True)
                    else:
                        # Get title from trafilatura or fallback
                        soup = BeautifulSoup(response.text, 'html.parser')
                        title = soup.title.string if soup.title else url
                
                # Clean the extracted text
                cleaned_text = self.text_cleaner.clean_text(extracted_text)
                
                # Truncate if too long (prevent GPT token issues)
                if len(cleaned_text) > 3000:
                    cleaned_text = cleaned_text[:3000]
                    logger.info(f"Truncated content from {url} to 3000 chars")
                
                # Rate limiting
                time.sleep(self.rate_limit_delay)
                
                return RawDoc(
                    url=url,
                    title=title,
                    text=cleaned_text,
                    source_type="website",
                    timestamp=datetime.now()
                )
                
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Failed to fetch {url} after {self.max_retries} attempts")
                    return None
    
    def find_subpages(self, base_url: str, homepage_soup: BeautifulSoup) -> List[str]:
        """Find common subpages from homepage links"""
        subpages = []
        candidates = [
            "about", "product", "pricing", "blog", "careers", "team", 
            "features", "solutions", "customers", "partners", "help",
            "docs", "api", "developers", "enterprise", "startups"
        ]
        
        # Find all links
        for link in homepage_soup.find_all('a', href=True):
            href = link['href'].lower()
            
            # Check for candidate keywords
            for candidate in candidates:
                if candidate in href:
                    full_url = urljoin(base_url, link['href'])
                    if full_url not in subpages and full_url != base_url:
                        subpages.append(full_url)
            
            # Also check for common patterns
            if any(pattern in href for pattern in ['/about', '/product', '/pricing', '/team']):
                full_url = urljoin(base_url, link['href'])
                if full_url not in subpages and full_url != base_url:
                    subpages.append(full_url)
        
        return subpages[:8]  # Limit to 8 subpages
    
    def scrape_company_website(self, website_url: str) -> List[RawDoc]:
        """Scrape homepage and common subpages"""
        docs = []
        
        # Scrape homepage
        homepage_doc = self.fetch_page(website_url)
        if homepage_doc:
            docs.append(homepage_doc)
            
            # Parse homepage to find subpages
            soup = BeautifulSoup(homepage_doc.text, 'html.parser')
            subpage_urls = self.find_subpages(website_url, soup)
            
            # Scrape subpages
            for subpage_url in subpage_urls[:5]:  # Limit to 5 subpages
                subpage_doc = self.fetch_page(subpage_url)
                if subpage_doc:
                    docs.append(subpage_doc)
        
        return docs
