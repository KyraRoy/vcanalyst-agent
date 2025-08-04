import re
import logging
from typing import List, Dict, Optional, Tuple
from models.schemas import Section, Citation
from datetime import datetime

logger = logging.getLogger(__name__)

def tag_paragraph_for_section(paragraph: str) -> Optional[str]:
    """Classify a paragraph into a memo section based on keywords."""
    keyword_groups = {
        "funding": ["raised", "valuation", "series", "funding", "capital", "$", "investors"],
        "traction": ["users", "maus", "growth", "downloads", "monthly", "adoption", "customers"],
        "problem": ["problem", "pain", "frustrating", "difficulty", "challenge"],
        "solution": ["solve", "our product", "we address", "enables", "platform helps"],
        "product": ["features", "dashboard", "ux", "tools", "functionality"],
        "business_model": ["pricing", "free", "pro", "enterprise", "revenue", "monetize"],
    }
    p = paragraph.lower()
    for section, keywords in keyword_groups.items():
        for kw in keywords:
            if kw in p:
                return section
    return None

class NLExtractor:
    def __init__(self):
        # Traction/financial patterns
        self.traction_patterns = [
            r'(\d[\d,\.]+)\s*(users|MAU|ARR|\$M|\$B|revenue|GMV|run rate|downloads|customers)',
            r'(\$\d[\d,\.]+)\s*(million|billion|M|B)\s*(revenue|funding|raised|ARR)',
            r'(\d[\d,\.]+)\s*(star|rating)',
            r'(trusted by|used by|powering)\s*([^\.]+)',
            r'(raised|secured)\s*(\$\d[\d,\.]+)\s*(million|billion|M|B)',
            r'(\d[\d,\.]+)\s*(countries|markets|partners)',
            r'(\d[\d,\.]+)\s*(employees|team members|developers)',
        ]
        
        # Problem/solution patterns
        self.problem_patterns = [
            r'(problem|challenge|pain point|struggle|difficulty|issue|frustration)',
            r'(customers|users|businesses|companies)\s+(struggle|face|deal with|suffer from|find it difficult)',
            r'(complex|complicated|difficult|hard|time-consuming|expensive)',
            r'(lack of|missing|need for|demand for)',
        ]
        
        self.solution_patterns = [
            r'(we solve|our solution|addresses|solves|fixes|resolves)',
            r'(enables|allows|helps|provides|delivers|offers)',
            r'(simplifies|streamlines|automates|optimizes)',
            r'(designed to|built to|created to)',
        ]
        
        # Business model patterns
        self.business_model_patterns = [
            r'(SaaS|subscription|monthly|annual|recurring|recurring revenue)',
            r'(marketplace|platform|commission|transaction|take rate)',
            r'(freemium|free tier|premium|upgrade|enterprise)',
            r'(API|enterprise|B2B|B2C|business-to-business)',
            r'(per seat|per user|usage-based|pay-as-you-go)',
        ]
        
        # Team patterns
        self.team_patterns = [
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s*[-–]\s*(CEO|CTO|COO|Founder|Co-founder|President)',
            r'(founded by|co-founded by|led by|CEO|CTO|COO)\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s*(CEO|CTO|COO|Founder|Co-founder)',
        ]
        
        # Product patterns
        self.product_patterns = [
            r'(platform|software|app|tool|solution|service)',
            r'(designed for|built for|targets|serves)',
            r'(features|capabilities|functionality)',
            r'(integrate|connect|sync|automate)',
        ]
    
    def extract_traction(self, text: str, citations: List[Citation]) -> Section:
        """Extract traction metrics and achievements"""
        metrics = {}
        bullets = []
        
        for pattern in self.traction_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) >= 2:
                    metric_name = match.group(2).upper()
                    metric_value = match.group(1)
                    metrics[metric_name] = metric_value
                    bullets.append(f"{metric_value} {metric_name}")
        
        # Look for traction-related sentences
        traction_sentences = []
        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:
                continue
                
            if any(word in sentence.lower() for word in [
                'users', 'revenue', 'growth', 'funding', 'raised', 'customers',
                'partners', 'countries', 'employees', 'downloads', 'reviews'
            ]):
                traction_sentences.append(sentence)
        
        return Section(
            text=". ".join(traction_sentences[:3]) if traction_sentences else None,
            bullets=bullets[:5],
            metrics=metrics,
            citations=citations
        )
    
    def extract_problem(self, text: str, citations: List[Citation]) -> Section:
        """Extract problem statements"""
        problem_sentences = []
        
        for pattern in self.problem_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Get the sentence containing the match
                sentence_start = text.rfind('.', 0, match.start()) + 1
                sentence_end = text.find('.', match.end())
                if sentence_end == -1:
                    sentence_end = len(text)
                
                sentence = text[sentence_start:sentence_end].strip()
                if len(sentence) > 30 and sentence not in problem_sentences:
                    problem_sentences.append(sentence)
        
        return Section(
            text=". ".join(problem_sentences[:2]) if problem_sentences else None,
            citations=citations
        )
    
    def extract_solution(self, text: str, citations: List[Citation]) -> Section:
        """Extract solution descriptions"""
        solution_sentences = []
        
        for pattern in self.solution_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Get the sentence containing the match
                sentence_start = text.rfind('.', 0, match.start()) + 1
                sentence_end = text.find('.', match.end())
                if sentence_end == -1:
                    sentence_end = len(text)
                
                sentence = text[sentence_start:sentence_end].strip()
                if len(sentence) > 30 and sentence not in solution_sentences:
                    solution_sentences.append(sentence)
        
        return Section(
            text=". ".join(solution_sentences[:2]) if solution_sentences else None,
            citations=citations
        )
    
    def extract_business_model(self, text: str, citations: List[Citation]) -> Section:
        """Extract business model information"""
        model_keywords = []
        
        for pattern in self.business_model_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                model_keywords.append(match.group(0))
        
        # Also look for pricing-related content
        pricing_indicators = [
            'free', 'premium', 'pro', 'enterprise', 'pricing', 'plans',
            'subscription', 'monthly', 'annual', 'per user', 'per seat',
            'usage-based', 'pay-as-you-go', 'freemium', 'tier'
        ]
        
        for indicator in pricing_indicators:
            if indicator in text.lower():
                model_keywords.append(indicator)
        
        if model_keywords:
            unique_models = list(set(model_keywords))
            return Section(
                text=f"Business model appears to be: {', '.join(unique_models)}",
                citations=citations
            )
        
        return Section(citations=citations)
    
    def extract_team(self, text: str, citations: List[Citation]) -> Section:
        """Extract team information"""
        team_members = []
        
        for pattern in self.team_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) >= 2:
                    name = match.group(1)
                    role = match.group(2)
                    team_members.append(f"{name} - {role}")
        
        return Section(
            bullets=team_members[:10],  # Limit to 10 team members
            citations=citations
        )
    
    def extract_product(self, text: str, citations: List[Citation]) -> Section:
        """Extract product information"""
        # Look for product-related sentences
        product_sentences = []
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 30:
                continue
                
            # Look for product descriptions
            if any(word in sentence.lower() for word in [
                'platform', 'app', 'software', 'tool', 'solution', 'product',
                'service', 'technology', 'system', 'workspace', 'workspace',
                'all-in-one', 'integrated', 'unified', 'centralized'
            ]):
                product_sentences.append(sentence)
            
            # Also look for "what we do" type descriptions
            elif any(phrase in sentence.lower() for phrase in [
                'helps you', 'enables you', 'allows you', 'lets you',
                'designed for', 'built for', 'created for', 'made for',
                'one place', 'single platform', 'everything you need'
            ]):
                product_sentences.append(sentence)
        
        return Section(
            text=". ".join(product_sentences[:3]) if product_sentences else None,
            citations=citations
        )
    
    def extract_intro(self, text: str, company_name: str, citations: List[Citation]) -> Section:
        """Extract company introduction"""
        # Look for the first meaningful paragraph about the company
        paragraphs = text.split('\n\n')
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if len(paragraph) < 50:
                continue
                
            if company_name.lower() in paragraph.lower():
                return Section(text=paragraph, citations=citations)
        
        # If no company-specific paragraph, take the first substantial paragraph
        for paragraph in paragraphs[:3]:
            paragraph = paragraph.strip()
            if len(paragraph) > 100:
                return Section(text=paragraph, citations=citations)
        
        return Section(citations=citations) 

    def extract_structured_fields(self, docs: list, company_name: str) -> dict:
        """Tag and aggregate paragraphs from docs into Section objects per field."""
        from models.schemas import Section, Citation
        from datetime import datetime
        sections = {k: Section() for k in ["funding", "traction", "problem", "solution", "product", "business_model"]}
        citations = {k: [] for k in sections}
        bullets = {k: [] for k in sections}
        for doc in docs:
            url = getattr(doc, 'url', None) or doc.get('url', None)
            title = getattr(doc, 'title', None) or doc.get('title', None)
            text = getattr(doc, 'text', None) or doc.get('text', None)
            source_type = getattr(doc, 'source_type', None) or doc.get('source_type', 'website')
            timestamp = getattr(doc, 'timestamp', None) or datetime.now()
            if not text:
                continue
            for paragraph in text.split('\n\n'):
                para = paragraph.strip()
                if len(para) < 30:
                    continue
                tag = tag_paragraph_for_section(para)
                if tag:
                    bullets[tag].append(para)
                    citations[tag].append(Citation(
                        url=url,
                        snippet=para[:200] + ("..." if len(para) > 200 else ""),
                        source_type=source_type,
                        timestamp=timestamp
                    ))
        # Build Section objects
        for tag in sections:
            if bullets[tag]:
                sections[tag].text = "\n".join(bullets[tag][:3])
                sections[tag].bullets = bullets[tag][:5]
                sections[tag].citations = citations[tag]
        # Only include sections with content and at least one citation
        return {k: v for k, v in sections.items() if v.text and v.citations} 