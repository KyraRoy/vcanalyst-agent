import os
import json
import logging
import time
from typing import List, Dict, Optional
from datetime import datetime
from openai import OpenAI
from models.schemas import RawDoc, Section, Citation

logger = logging.getLogger(__name__)

# Load OpenAI API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    logger.warning("OPENAI_API_KEY not found in environment variables")

def chunk_text(text: str, max_chunk_size: int = 4000) -> List[str]:
    """Split text into chunks that fit within token limits"""
    if len(text) <= max_chunk_size:
        return [text]
    
    chunks = []
    paragraphs = text.split('\n\n')
    current_chunk = ""
    
    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) < max_chunk_size:
            current_chunk += paragraph + '\n\n'
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = paragraph + '\n\n'
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def create_extraction_prompt(company_name: str, chunk: Dict) -> str:
    """Create the prompt for GPT-4 section extraction"""
    return f"""Company: {company_name}
Source URL: {chunk['url']}
Source Title: {chunk['title']}

TEXT:
\"\"\"{chunk['text']}\"\"\"

Instructions:
You are a professional VC analyst. Extract ONLY information that is directly found in the source text above. Do not make assumptions or add external knowledge.

For each of the following sections, return ONLY if relevant information is found in the source text:

1. introduction - Company overview, what they do, mission
2. problem - Pain points they solve, market problems
3. solution - How they solve the problem, their approach
4. product - Features, functionality, how it works
5. traction - Users, growth, metrics, milestones
6. business_model - Revenue model, pricing, monetization
7. market - Market size, opportunity, TAM/SAM/SOM
8. team - Founders, key team members, experience
9. competition - Competitors, alternatives, differentiation
10. funding - Investment rounds, valuation, investors
11. financials - Revenue, costs, projections
12. why_now - Market timing, trends, catalysts

Format output as JSON:
{{
  "section_name": {{
    "text": "Brief summary of relevant information",
    "bullets": ["Key point 1", "Key point 2"],
    "citation": "{chunk['url']}"
  }}
}}

If no relevant information is found for a section, omit it entirely.
Return only valid JSON with no additional text.
"""

def extract_from_chunk(company_name: str, chunk: Dict, max_retries: int = 3) -> Dict:
    """Extract sections from a single chunk using GPT-4"""
    try:
        prompt = create_extraction_prompt(company_name, chunk)
        
        for attempt in range(max_retries):
            try:
                client = OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[
                        {
                            "role": "system", 
                            "content": "You are a professional VC analyst. Only extract insights that are directly found in the source text. Return only valid JSON with no additional text."
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    temperature=0.3,
                    max_tokens=2000
                )
                
                # Parse the response
                content = response.choices[0].message.content.strip()
                
                # Try to extract JSON from the response
                if content.startswith('{') and content.endswith('}'):
                    result = json.loads(content)
                    logger.info(f"Successfully extracted sections from {chunk['url']}")
                    return result
                else:
                    # Try to find JSON within the response
                    start_idx = content.find('{')
                    end_idx = content.rfind('}') + 1
                    if start_idx != -1 and end_idx > start_idx:
                        json_str = content[start_idx:end_idx]
                        result = json.loads(json_str)
                        logger.info(f"Successfully extracted sections from {chunk['url']}")
                        return result
                    else:
                        logger.warning(f"No valid JSON found in response from {chunk['url']}")
                        return {}
                        
            except json.JSONDecodeError as e:
                logger.warning(f"JSON decode error on attempt {attempt + 1} for {chunk['url']}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Failed to parse JSON after {max_retries} attempts for {chunk['url']}")
                    return {}
                    
            except Exception as e:
                logger.warning(f"API error on attempt {attempt + 1} for {chunk['url']}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Failed to extract from {chunk['url']} after {max_retries} attempts")
                    return {}
                    
    except Exception as e:
        logger.error(f"Unexpected error processing {chunk['url']}: {e}")
        return {}

def merge_section_results(all_results: List[Dict]) -> Dict[str, Section]:
    """Merge multiple chunk results into final Section objects"""
    merged_sections = {}
    
    for result in all_results:
        for section_name, section_data in result.items():
            if section_name not in merged_sections:
                merged_sections[section_name] = {
                    'text': [],
                    'bullets': [],
                    'citations': []
                }
            
            # Add text if present
            if 'text' in section_data and section_data['text']:
                merged_sections[section_name]['text'].append(section_data['text'])
            
            # Add bullets if present
            if 'bullets' in section_data and section_data['bullets']:
                merged_sections[section_name]['bullets'].extend(section_data['bullets'])
            
            # Add citation if present
            if 'citation' in section_data and section_data['citation']:
                merged_sections[section_name]['citations'].append(section_data['citation'])
    
    # Convert to Section objects
    final_sections = {}
    for section_name, data in merged_sections.items():
        # Combine text with newlines
        combined_text = '\n\n'.join(data['text']) if data['text'] else None
        
        # Remove duplicate bullets
        unique_bullets = list(dict.fromkeys(data['bullets'])) if data['bullets'] else []
        
        # Create citations
        citations = []
        for url in data['citations']:
            citations.append(Citation(
                url=url,
                snippet=f"Extracted from {section_name} section",
                source_type="website",
                timestamp=datetime.now()
            ))
        
        final_sections[section_name] = Section(
            text=combined_text,
            bullets=unique_bullets,
            citations=citations
        )
    
    return final_sections

def extract_sections_with_gpt(company_name: str, raw_docs: List[RawDoc]) -> Dict[str, Section]:
    """
    Extract structured memo sections from raw documents using GPT-4.
    
    Args:
        company_name: Name of the company being analyzed
        raw_docs: List of RawDoc objects from various sources
        
    Returns:
        Dictionary mapping section names to Section objects
    """
    if not api_key:
        logger.error("OPENAI_API_KEY not found. Cannot perform GPT-4 extraction.")
        return {}
    
    logger.info(f"Starting GPT-4 extraction for {company_name} with {len(raw_docs)} documents")
    
    # Prepare chunks from raw documents
    chunks = []
    for doc in raw_docs:
        if not doc.text or len(doc.text.strip()) < 50:
            continue  # Skip very short documents
            
        # Split long documents into chunks
        text_chunks = chunk_text(doc.text)
        
        for i, text_chunk in enumerate(text_chunks):
            chunk = {
                "text": text_chunk,
                "url": str(doc.url),
                "title": doc.title or "Unknown"
            }
            chunks.append(chunk)
    
    logger.info(f"Created {len(chunks)} chunks for processing")
    
    # Process chunks with rate limiting
    all_results = []
    for i, chunk in enumerate(chunks):
        logger.info(f"Processing chunk {i+1}/{len(chunks)} from {chunk['url']}")
        
        result = extract_from_chunk(company_name, chunk)
        if result:
            all_results.append(result)
        
        # Rate limiting - wait between requests
        if i < len(chunks) - 1:  # Don't wait after the last chunk
            time.sleep(1)  # 1 second between requests
    
    # Merge results into final sections
    final_sections = merge_section_results(all_results)
    
    # Log summary
    populated_sections = [name for name, section in final_sections.items() if section.has_content()]
    logger.info(f"Extraction complete. Found data for {len(populated_sections)} sections: {populated_sections}")
    
    return final_sections

def extract_sections_with_gpt_cached(company_name: str, raw_docs: List[RawDoc], cache_dir: str = "cache") -> Dict[str, Section]:
    """
    Cached version of extract_sections_with_gpt to avoid re-processing same documents.
    """
    import hashlib
    
    # Create cache directory if it doesn't exist
    os.makedirs(cache_dir, exist_ok=True)
    
    # Create cache key based on company name and document URLs
    cache_key = f"{company_name}_{hashlib.md5(str([doc.url for doc in raw_docs]).encode()).hexdigest()}"
    cache_file = os.path.join(cache_dir, f"{cache_key}.json")
    
    # Check if cached result exists
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
            
            # Convert back to Section objects
            sections = {}
            for section_name, section_data in cached_data.items():
                citations = []
                for citation_data in section_data.get('citations', []):
                    citations.append(Citation(**citation_data))
                
                sections[section_name] = Section(
                    text=section_data.get('text'),
                    bullets=section_data.get('bullets', []),
                    citations=citations
                )
            
            logger.info(f"Loaded cached extraction results for {company_name}")
            return sections
            
        except Exception as e:
            logger.warning(f"Failed to load cache for {company_name}: {e}")
    
    # Perform extraction
    sections = extract_sections_with_gpt(company_name, raw_docs)
    
    # Cache the results
    try:
        cache_data = {}
        for section_name, section in sections.items():
            cache_data[section_name] = {
                'text': section.text,
                'bullets': section.bullets,
                'citations': [citation.model_dump() for citation in section.citations]
            }
        
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
        
        logger.info(f"Cached extraction results for {company_name}")
        
    except Exception as e:
        logger.warning(f"Failed to cache results for {company_name}: {e}")
    
    return sections 