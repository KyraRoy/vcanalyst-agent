import logging
import os
import json
import re
from typing import Dict, List, Optional
from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import openai
from datetime import datetime

from models.schemas import Section, Citation

logger = logging.getLogger(__name__)

def extract_slide_data(pdf_path: str) -> List[Dict]:
    """
    Extract text and image content from each slide of a pitch deck PDF.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of slide data with text and OCR content
    """
    logger.info(f"Extracting slide data from {pdf_path}")
    
    try:
        doc = fitz.open(pdf_path)
        slides = []
        
        for page_num, page in enumerate(doc):
            logger.info(f"Processing slide {page_num + 1}")
            
            # Extract text content using different methods
            text_content = extract_text_from_page(page)
            image_content = extract_images_from_page(page)
            
            # Combine all content
            combined_content = combine_slide_content(text_content, image_content, page_num + 1)
            
            if combined_content.strip():
                slides.append({
                    "slide_number": page_num + 1,
                    "text": combined_content,
                    "raw_text": text_content,
                    "image_content": image_content
                })
        
        doc.close()
        logger.info(f"Extracted data from {len(slides)} slides")
        return slides
        
    except Exception as e:
        logger.error(f"Failed to extract slide data from {pdf_path}: {e}")
        return []

def extract_text_from_page(page) -> str:
    """
    Extract text content from a PDF page using multiple methods.
    
    Args:
        page: PyMuPDF page object
        
    Returns:
        Extracted text content
    """
    try:
        # Method 1: Get text blocks (more structured)
        text_blocks = page.get_text("blocks")
        text_content = []
        
        for block in text_blocks:
            if block[6] == 0:  # Text block
                text_content.append(block[4])
        
        # Method 2: Get raw text as fallback
        raw_text = page.get_text("text").strip()
        
        # Combine both methods
        structured_text = "\n".join(text_content).strip()
        if structured_text:
            return structured_text
        else:
            return raw_text
            
    except Exception as e:
        logger.warning(f"Text extraction failed: {e}")
        return ""

def extract_images_from_page(page) -> str:
    """
    Extract image content from a PDF page using OCR.
    
    Args:
        page: PyMuPDF page object
        
    Returns:
        OCR text from images
    """
    try:
        # Convert page to high-resolution image
        matrix = fitz.Matrix(2, 2)  # 2x zoom for better OCR
        pix = page.get_pixmap(matrix=matrix)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # Perform OCR with better configuration
        custom_config = r'--oem 3 --psm 6'  # Use LSTM OCR Engine + Assume uniform block of text
        ocr_text = pytesseract.image_to_string(img, config=custom_config).strip()
        
        # Clean OCR text
        if ocr_text:
            # Remove common OCR artifacts
            ocr_text = re.sub(r'[^\w\s\.\,\-\$\%\d]', ' ', ocr_text)
            ocr_text = re.sub(r'\s+', ' ', ocr_text).strip()
            
            return ocr_text
        else:
            return ""
            
    except Exception as e:
        logger.warning(f"Image OCR failed: {e}")
        return ""

def combine_slide_content(text_content: str, image_content: str, slide_number: int) -> str:
    """
    Combine text and image content into a structured format for GPT analysis.
    
    Args:
        text_content: Extracted text from the slide
        image_content: OCR text from images
        slide_number: Slide number
        
    Returns:
        Combined content in structured format
    """
    # Extract potential slide title (first few lines)
    lines = text_content.split('\n')
    potential_title = ""
    if lines:
        potential_title = lines[0].strip()
        if len(potential_title) > 50:  # Too long for a title
            potential_title = ""
    
    # Build structured content
    structured_content = f"Slide {slide_number}"
    if potential_title:
        structured_content += f": {potential_title}"
    
    structured_content += "\n\n"
    
    # Add text content
    if text_content:
        structured_content += f"Text Content:\n{text_content}\n\n"
    
    # Add image content
    if image_content:
        structured_content += f"Image/Visual Content:\n{image_content}\n\n"
    
    return structured_content.strip()

def clean_slide_text(text: str) -> str:
    """
    Clean and filter slide text content.
    
    Args:
        text: Raw slide text
        
    Returns:
        Cleaned text content
    """
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove common slide artifacts
    text = re.sub(r'Page \d+ of \d+', '', text)
    text = re.sub(r'Slide \d+', '', text)
    
    # Remove very short lines (likely artifacts)
    lines = text.split('\n')
    cleaned_lines = [line.strip() for line in lines if len(line.strip()) > 3]
    
    return '\n'.join(cleaned_lines).strip()

def create_slide_analysis_prompt(slide_number: int, slide_text: str) -> str:
    """
    Create a GPT-4 prompt for analyzing a single slide with structured content.
    
    Args:
        slide_number: Slide number
        slide_text: Structured content from the slide (text + image OCR)
        
    Returns:
        Formatted prompt for GPT-4
    """
    return f"""
You are a venture capital analyst reviewing a startup pitch deck.

Here is the structured content from slide {slide_number}:

--- SLIDE CONTENT START ---
{slide_text}
--- SLIDE CONTENT END ---

Analyze this slide and extract any relevant information about the startup's:

1. **Problem** - What problem is the startup solving?
2. **Solution** - How does the startup solve this problem?
3. **Product** - What is the product/service offering?
4. **Business Model** - How does the startup make money?
5. **Traction** - What are the key metrics and growth indicators?
6. **Funding** - What funding is being sought or has been raised?
7. **Team** - Information about founders and key team members
8. **Market** - Market size, opportunity, and target market
9. **Competition** - Competitive landscape and positioning
10. **Financials** - Revenue, projections, or financial metrics
11. **Growth Strategy** - Go-to-market strategy and expansion plans
12. **Vision** - Long-term vision and goals

Pay special attention to:
- Numbers and metrics (users, revenue, market size, funding amounts)
- Visual content like charts, graphs, and diagrams
- Slide titles and headers that indicate the topic
- Bullet points and key messaging

If the slide contains relevant information for any of these sections, extract it into structured format.
If no relevant information is found, return an empty result.

Return ONLY valid JSON in this exact format:
{{
  "problem": {{"text": "description", "bullets": ["point1", "point2"], "citations": ["Pitch Deck Slide {slide_number}"]}},
  "solution": {{"text": "description", "bullets": ["point1", "point2"], "citations": ["Pitch Deck Slide {slide_number}"]}},
  "product": {{"text": "description", "bullets": ["point1", "point2"], "citations": ["Pitch Deck Slide {slide_number}"]}},
  "business_model": {{"text": "description", "bullets": ["point1", "point2"], "citations": ["Pitch Deck Slide {slide_number}"]}},
  "traction": {{"text": "description", "bullets": ["point1", "point2"], "citations": ["Pitch Deck Slide {slide_number}"]}},
  "funding": {{"text": "description", "bullets": ["point1", "point2"], "citations": ["Pitch Deck Slide {slide_number}"]}},
  "team": {{"text": "description", "bullets": ["point1", "point2"], "citations": ["Pitch Deck Slide {slide_number}"]}},
  "market": {{"text": "description", "bullets": ["point1", "point2"], "citations": ["Pitch Deck Slide {slide_number}"]}},
  "competition": {{"text": "description", "bullets": ["point1", "point2"], "citations": ["Pitch Deck Slide {slide_number}"]}},
  "financials": {{"text": "description", "bullets": ["point1", "point2"], "citations": ["Pitch Deck Slide {slide_number}"]}},
  "growth_strategy": {{"text": "description", "bullets": ["point1", "point2"], "citations": ["Pitch Deck Slide {slide_number}"]}},
  "vision": {{"text": "description", "bullets": ["point1", "point2"], "citations": ["Pitch Deck Slide {slide_number}"]}}
}}

Only include sections that have actual content. For empty sections, omit them entirely.
Focus on extracting specific, actionable information rather than generic statements.
"""

def analyze_slide_with_gpt(slide_number: int, slide_text: str) -> Dict:
    """
    Analyze a single slide using GPT-4.
    
    Args:
        slide_number: Slide number
        slide_text: Text content from the slide
        
    Returns:
        Dictionary of extracted sections
    """
    try:
        # Check if OpenAI API key is available
        if not os.getenv("OPENAI_API_KEY"):
            logger.warning("OPENAI_API_KEY not found. Cannot perform GPT-4 analysis.")
            return {}
        
        prompt = create_slide_analysis_prompt(slide_number, slide_text)
        
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional VC analyst. Extract only factual information from pitch deck slides. Be concise and accurate."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        content = response.choices[0].message.content.strip()
        
        # Parse JSON response
        try:
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
            
            logger.info(f"Successfully analyzed slide {slide_number}")
            return result
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse GPT-4 response for slide {slide_number}: {e}")
            return {}
            
    except Exception as e:
        logger.warning(f"GPT-4 analysis failed for slide {slide_number}: {e}")
        return {}

def analyze_slide_with_rules(slide_number: int, slide_text: str) -> Dict:
    """
    Analyze a single slide using rule-based extraction when GPT-4 is not available.
    
    Args:
        slide_number: Slide number
        slide_text: Text content from the slide
        
    Returns:
        Dictionary of extracted sections
    """
    logger.info(f"Using rule-based analysis for slide {slide_number}")
    
    result = {}
    text_lower = slide_text.lower()
    
    # Problem section detection
    problem_keywords = ['problem', 'challenge', 'issue', 'pain point', 'struggle', 'difficulty', 'frustration']
    if any(keyword in text_lower for keyword in problem_keywords):
        # Extract sentences containing problem keywords
        sentences = slide_text.split('.')
        problem_sentences = []
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in problem_keywords):
                problem_sentences.append(sentence.strip())
        
        if problem_sentences:
            result['problem'] = {
                'text': '. '.join(problem_sentences[:2]),  # Limit to 2 sentences
                'bullets': [s.strip() for s in problem_sentences[:3]],
                'citations': [f"slide_{slide_number}"]
            }
    
    # Solution section detection
    solution_keywords = ['solution', 'solve', 'address', 'enable', 'provide', 'offer', 'platform', 'product']
    if any(keyword in text_lower for keyword in solution_keywords):
        sentences = slide_text.split('.')
        solution_sentences = []
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in solution_keywords):
                solution_sentences.append(sentence.strip())
        
        if solution_sentences:
            result['solution'] = {
                'text': '. '.join(solution_sentences[:2]),
                'bullets': [s.strip() for s in solution_sentences[:3]],
                'citations': [f"slide_{slide_number}"]
            }
    
    # Team section detection
    team_keywords = ['team', 'founder', 'ceo', 'cto', 'coo', 'founders', 'leadership']
    if any(keyword in text_lower for keyword in team_keywords):
        sentences = slide_text.split('.')
        team_sentences = []
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in team_keywords):
                team_sentences.append(sentence.strip())
        
        if team_sentences:
            result['team'] = {
                'text': '. '.join(team_sentences[:2]),
                'bullets': [s.strip() for s in team_sentences[:3]],
                'citations': [f"slide_{slide_number}"]
            }
    
    # Market section detection
    market_keywords = ['market', 'tam', 'sam', 'som', 'opportunity', 'size', 'billion', 'million']
    if any(keyword in text_lower for keyword in market_keywords):
        sentences = slide_text.split('.')
        market_sentences = []
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in market_keywords):
                market_sentences.append(sentence.strip())
        
        if market_sentences:
            result['market'] = {
                'text': '. '.join(market_sentences[:2]),
                'bullets': [s.strip() for s in market_sentences[:3]],
                'citations': [f"slide_{slide_number}"]
            }
    
    # Traction section detection
    traction_keywords = ['users', 'customers', 'growth', 'revenue', 'funding', 'raised', 'million', 'billion', 'users']
    if any(keyword in text_lower for keyword in traction_keywords):
        sentences = slide_text.split('.')
        traction_sentences = []
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in traction_keywords):
                traction_sentences.append(sentence.strip())
        
        if traction_sentences:
            result['traction'] = {
                'text': '. '.join(traction_sentences[:2]),
                'bullets': [s.strip() for s in traction_sentences[:3]],
                'citations': [f"slide_{slide_number}"]
            }
    
    # Product section detection
    product_keywords = ['product', 'feature', 'platform', 'app', 'software', 'tool', 'service']
    if any(keyword in text_lower for keyword in product_keywords):
        sentences = slide_text.split('.')
        product_sentences = []
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in product_keywords):
                product_sentences.append(sentence.strip())
        
        if product_sentences:
            result['product'] = {
                'text': '. '.join(product_sentences[:2]),
                'bullets': [s.strip() for s in product_sentences[:3]],
                'citations': [f"slide_{slide_number}"]
            }
    
    # Business model section detection
    business_keywords = ['business model', 'revenue', 'pricing', 'monetization', 'saas', 'subscription', 'freemium']
    if any(keyword in text_lower for keyword in business_keywords):
        sentences = slide_text.split('.')
        business_sentences = []
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in business_keywords):
                business_sentences.append(sentence.strip())
        
        if business_sentences:
            result['business_model'] = {
                'text': '. '.join(business_sentences[:2]),
                'bullets': [s.strip() for s in business_sentences[:3]],
                'citations': [f"slide_{slide_number}"]
            }
    
    # Growth strategy section detection
    growth_keywords = ['growth', 'strategy', 'go-to-market', 'acquisition', 'partnership', 'expansion', 'scale']
    if any(keyword in text_lower for keyword in growth_keywords):
        sentences = slide_text.split('.')
        growth_sentences = []
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in growth_keywords):
                growth_sentences.append(sentence.strip())
        
        if growth_sentences:
            result['growth_strategy'] = {
                'text': '. '.join(growth_sentences[:2]),
                'bullets': [s.strip() for s in growth_sentences[:3]],
                'citations': [f"slide_{slide_number}"]
            }
    
    # Financials section detection
    financial_keywords = ['financial', 'revenue', 'funding', 'investment', 'series', 'valuation', 'burn rate', 'runway']
    if any(keyword in text_lower for keyword in financial_keywords):
        sentences = slide_text.split('.')
        financial_sentences = []
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in financial_keywords):
                financial_sentences.append(sentence.strip())
        
        if financial_sentences:
            result['financials'] = {
                'text': '. '.join(financial_sentences[:2]),
                'bullets': [s.strip() for s in financial_sentences[:3]],
                'citations': [f"slide_{slide_number}"]
            }
    
    # Risks section detection
    risk_keywords = ['risk', 'challenge', 'threat', 'competition', 'regulatory', 'execution']
    if any(keyword in text_lower for keyword in risk_keywords):
        sentences = slide_text.split('.')
        risk_sentences = []
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in risk_keywords):
                risk_sentences.append(sentence.strip())
        
        if risk_sentences:
            result['risks'] = {
                'text': '. '.join(risk_sentences[:2]),
                'bullets': [s.strip() for s in risk_sentences[:3]],
                'citations': [f"slide_{slide_number}"]
            }
    
    # Timing/Why Now section detection
    timing_keywords = ['timing', 'now', 'trend', 'market timing', 'opportunity', 'momentum', 'wave']
    if any(keyword in text_lower for keyword in timing_keywords):
        sentences = slide_text.split('.')
        timing_sentences = []
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in timing_keywords):
                timing_sentences.append(sentence.strip())
        
        if timing_sentences:
            result['timing'] = {
                'text': '. '.join(timing_sentences[:2]),
                'bullets': [s.strip() for s in timing_sentences[:3]],
                'citations': [f"slide_{slide_number}"]
            }
    
    # Moat/Defensibility section detection
    moat_keywords = ['moat', 'defensibility', 'competitive advantage', 'barrier', 'network effect', 'proprietary', 'ip']
    if any(keyword in text_lower for keyword in moat_keywords):
        sentences = slide_text.split('.')
        moat_sentences = []
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in moat_keywords):
                moat_sentences.append(sentence.strip())
        
        if moat_sentences:
            result['moat'] = {
                'text': '. '.join(moat_sentences[:2]),
                'bullets': [s.strip() for s in moat_sentences[:3]],
                'citations': [f"slide_{slide_number}"]
            }
    
    return result

def merge_slide_results(all_slide_results: List[Dict]) -> Dict[str, Section]:
    """
    Merge results from all slides into a final structured format.
    
    Args:
        all_slide_results: List of slide analysis results
        
    Returns:
        Dictionary of merged Section objects
    """
    logger.info("Merging slide analysis results")
    
    # Initialize merged sections
    merged_sections = {}
    
    # Define all possible sections
    section_names = [
        'problem', 'solution', 'product', 'business_model', 'traction',
        'funding', 'team', 'market', 'competition', 'financials'
    ]
    
    for section_name in section_names:
        section_texts = []
        section_bullets = []
        section_citations = []
        
        # Collect all data for this section from all slides
        for slide_result in all_slide_results:
            if section_name in slide_result:
                section_data = slide_result[section_name]
                
                if section_data.get('text'):
                    section_texts.append(section_data['text'])
                
                if section_data.get('bullets'):
                    section_bullets.extend(section_data['bullets'])
                
                if section_data.get('citations'):
                    section_citations.extend(section_data['citations'])
        
        # Create Section object if we have content
        if section_texts or section_bullets:
            # Merge text content
            merged_text = ' '.join(section_texts) if section_texts else ""
            
            # Remove duplicate bullets
            unique_bullets = list(dict.fromkeys(section_bullets))
            
            # Create citations
            citations = []
            for citation_text in section_citations:
                citations.append(Citation(
                    url=f"https://pitch_deck_slide_{citation_text.split()[-1]}.pdf",
                    snippet=f"Pitch deck content",
                    source_type="pitch_deck",
                    timestamp=datetime.now()
                ))
            
            merged_sections[section_name] = Section(
                text=merged_text,
                bullets=unique_bullets,
                citations=citations
            )
    
    logger.info(f"Merged {len(merged_sections)} sections from pitch deck")
    return merged_sections

def parse_pitch_deck(pdf_path: str) -> Dict[str, Section]:
    """
    Extracts structured investment memo data from a pitch deck PDF with both text and image content.

    Args:
        pdf_path (str): Path to the uploaded pitch deck.
    
    Returns:
        Dict[str, Section]: Mapping of memo section names to Section objects (text, bullets, citations).
    """
    logger.info(f"Starting pitch deck analysis for {pdf_path}")
    
    # Validate file exists
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        return {}
    
    # Step 1: Extract slide data (text + OCR)
    slides = extract_slide_data(pdf_path)
    
    if not slides:
        logger.warning("No slides could be extracted from the PDF")
        return {}
    
    # Step 2: Try enhanced GPT-4 analysis first
    try:
        from agents.enhanced_analyzer import EnhancedAnalyzer
        
        if os.getenv("OPENAI_API_KEY"):
            logger.info("Using enhanced GPT-4 analysis")
            analyzer = EnhancedAnalyzer()
            
            # Extract company name from first slide or filename
            company_name = extract_company_name_from_slides(slides, pdf_path)
            
            # Use enhanced GPT-4 analysis
            sections = analyzer.analyze_pitch_deck_with_gpt(slides, company_name)
            
            if sections:
                logger.info(f"Enhanced GPT-4 analysis successful: {len(sections)} sections")
                return sections
            else:
                logger.warning("Enhanced GPT-4 analysis returned no sections, falling back to rule-based")
        else:
            logger.warning("OPENAI_API_KEY not found, using rule-based analysis")
    except Exception as e:
        logger.warning(f"Enhanced analysis failed: {e}, falling back to rule-based")
    
    # Step 3: Fallback to rule-based analysis
    all_slide_results = []
    
    for slide in slides:
        logger.info(f"Analyzing slide {slide['slide_number']}")
        
        # Try GPT-4 first, fallback to rule-based if not available
        slide_result = analyze_slide_with_gpt(
            slide['slide_number'],
            slide['text']
        )
        
        # If GPT-4 failed, try rule-based analysis
        if not slide_result:
            slide_result = analyze_slide_with_rules(
                slide['slide_number'],
                slide['text']
            )
        
        if slide_result:
            all_slide_results.append(slide_result)
    
    # Step 4: Merge all slide results
    if all_slide_results:
        merged_sections = merge_slide_results(all_slide_results)
        logger.info(f"Successfully parsed pitch deck into {len(merged_sections)} sections")
        return merged_sections
    else:
        logger.warning("No content could be extracted from the pitch deck")
        return {}

def extract_company_name_from_slides(slides: List[Dict], pdf_path: str) -> str:
    """Extract company name from slides or filename"""
    # Try to extract from first slide
    if slides and slides[0].get('text'):
        first_slide_text = slides[0]['text'].lower()
        
        # Look for common company name patterns
        lines = first_slide_text.split('\n')
        for line in lines:
            line = line.strip()
            if len(line) > 2 and len(line) < 50:
                # Check if it looks like a company name (capitalized, not too long)
                if line[0].isupper() and not any(word in line.lower() for word in ['slide', 'page', 'the', 'and', 'or']):
                    return line.title()
    
    # Fallback to filename
    filename = os.path.basename(pdf_path)
    name = os.path.splitext(filename)[0]
    return name.replace('_', ' ').replace('-', ' ').title()

def get_pitch_deck_summary(pdf_path: str) -> Dict:
    """
    Get a high-level summary of the pitch deck content.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Dictionary with summary information
    """
    slides = extract_slide_data(pdf_path)
    
    if not slides:
        return {"error": "No slides could be extracted"}
    
    # Analyze slide titles and content patterns
    slide_titles = []
    content_patterns = []
    
    for slide in slides:
        # Extract potential slide titles (first few lines)
        lines = slide['text'].split('\n')
        if lines:
            potential_title = lines[0].strip()
            if len(potential_title) < 100 and potential_title:
                slide_titles.append(f"Slide {slide['slide_number']}: {potential_title}")
        
        # Analyze content patterns
        text = slide['text'].lower()
        if any(word in text for word in ['problem', 'challenge', 'issue']):
            content_patterns.append('problem')
        if any(word in text for word in ['solution', 'product', 'service']):
            content_patterns.append('solution')
        if any(word in text for word in ['market', 'size', 'opportunity']):
            content_patterns.append('market')
        if any(word in text for word in ['team', 'founder', 'ceo']):
            content_patterns.append('team')
        if any(word in text for word in ['funding', 'investment', 'raise']):
            content_patterns.append('funding')
        if any(word in text for word in ['traction', 'growth', 'users', 'revenue']):
            content_patterns.append('traction')
    
    return {
        "total_slides": len(slides),
        "slide_titles": slide_titles[:5],  # First 5 titles
        "content_patterns": list(set(content_patterns)),
        "has_images": any(slide.get('ocr_text') for slide in slides)
    } 