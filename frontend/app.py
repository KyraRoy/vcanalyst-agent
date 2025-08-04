import streamlit as st
import sys
import os
import json
import re
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add the parent directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Debug: Check if API key is available
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("❌ OPENAI_API_KEY not found in environment variables")
    st.info("Please check your Streamlit Cloud secrets configuration")
else:
    st.success(f"✅ OpenAI API key found: {api_key[:20]}...")

from agents.enhanced_analyzer import EnhancedAnalyzer
from agents.memo_generator import generate_memo
from agents.pitchdeck_parser import parse_pitch_deck, get_pitch_deck_summary
from models.schemas import StructuredCompanyDoc
from utils.pdf_generator import generate_pdf_bytes

# Configure page
st.set_page_config(
    page_title="VC Analyst Agent",
    page_icon="📊",
    layout="wide"
)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_company' not in st.session_state:
    st.session_state.current_company = None
if 'current_memo' not in st.session_state:
    st.session_state.current_memo = None
if 'current_doc' not in st.session_state:
    st.session_state.current_doc = None

def extract_company_name(query: str) -> str:
    """Extract company name from user query"""
    # Common patterns for company analysis
    patterns = [
        r"analyze\s+(\w+)",
        r"what's\s+(\w+)'s",
        r"(\w+)'s\s+(business model|traction|team|competitors|funding)",
        r"tell me about\s+(\w+)",
        r"research\s+(\w+)"
    ]
    
    query_lower = query.lower()
    for pattern in patterns:
        match = re.search(pattern, query_lower)
        if match:
            return match.group(1).title()
    
    # If no pattern matches, try to extract a capitalized word
    words = query.split()
    for word in words:
        if word[0].isupper() and len(word) > 2:
            return word
    
    return None

def get_section_content(doc: StructuredCompanyDoc, section_name: str) -> str:
    """Get content from a specific section of the memo"""
    if not hasattr(doc, section_name):
        return f"Section '{section_name}' not found."
    
    section = getattr(doc, section_name)
    if not section.has_content():
        return f"No data available for {section_name}."
    
    content = []
    if section.text:
        content.append(section.text)
    
    if section.bullets:
        content.append("\n**Key Points:**")
        for bullet in section.bullets:
            content.append(f"• {bullet}")
    
    if section.metrics:
        content.append("\n**Metrics:**")
        for metric, value in section.metrics.items():
            content.append(f"• {metric}: {value}")
    
    if section.citations:
        content.append("\n**Sources:**")
        for citation in section.citations:
            content.append(f"• [{citation.source_type}]({citation.url})")
    
    return "\n".join(content)

def run_full_analysis(company_name: str) -> StructuredCompanyDoc:
    """Run the full analysis pipeline for a company using enhanced analyzer"""
    analyzer = EnhancedAnalyzer()
    return analyzer.generate_memo_from_web_research(company_name)

def generate_markdown(doc: StructuredCompanyDoc) -> str:
    """Generate markdown from the company document"""
    return generate_memo(doc)

def handle_company_analysis(company_name: str):
    """Handle company analysis and update session state"""
    try:
        # Check if API key is available
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            st.error("❌ OPENAI_API_KEY not found. Please check your Streamlit Cloud secrets.")
            return None, None
        
        with st.spinner(f"Analyzing {company_name}..."):
            # Add debug info
            st.info(f"🔍 Starting analysis for {company_name}...")
            
            doc = run_full_analysis(company_name)
            
            if not doc:
                st.error("❌ Analysis failed - no document generated")
                return None, None
            
            memo = generate_markdown(doc)
            
            if not memo or len(memo) < 100:
                st.error("❌ Memo generation failed - content too short")
                return None, None
            
            st.session_state.current_company = company_name
            st.session_state.current_doc = doc
            st.session_state.current_memo = memo
            
            st.success(f"✅ Analysis complete for {company_name}!")
            return doc, memo
            
    except Exception as e:
        st.error(f"❌ Error analyzing {company_name}: {str(e)}")
        st.info("This might be due to API key issues or network problems.")
        return None, None

def handle_question(query: str, company_name: str):
    """Handle specific questions about a company"""
    if not st.session_state.current_doc:
        st.error("No company has been analyzed yet. Please analyze a company first.")
        return
    
    doc = st.session_state.current_doc
    
    # Extract section name from query
    query_lower = query.lower()
    sections = ['problem', 'solution', 'team', 'market', 'traction', 'competitors', 'business model', 'financials']
    
    for section in sections:
        if section in query_lower:
            content = get_section_content(doc, section.replace(' ', '_'))
            return content
    
    # If no specific section found, return general info
    return f"Here's what I know about {company_name}:\n\n{st.session_state.current_memo[:500]}..."

def process_pitch_deck(uploaded_file):
    """Process uploaded pitch deck"""
    try:
        with st.spinner("Analyzing pitch deck..."):
            # Save uploaded file temporarily
            temp_path = f"temp_pitch_deck.pdf"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Parse pitch deck
            sections = parse_pitch_deck(temp_path)
            
            if sections:
                # Create company document
                company_name = "Pitch Deck Company"  # You could extract this from the deck
                doc = StructuredCompanyDoc(name=company_name)
                
                # Apply sections to document
                for section_name, section_data in sections.items():
                    if hasattr(doc, section_name):
                        setattr(doc, section_name, section_data)
                
                # Generate memo
                memo = generate_memo(doc)
                
                st.session_state.current_company = company_name
                st.session_state.current_doc = doc
                st.session_state.current_memo = memo
                
                return doc, memo
            else:
                st.error("Could not extract meaningful content from the pitch deck.")
                return None, None
                
    except Exception as e:
        st.error(f"Error processing pitch deck: {str(e)}")
        return None, None

def main():
    st.title("🤖 VC Analyst Agent")
    st.markdown("**Your AI-powered investment analysis assistant**")
    
    # Display current company if available
    if st.session_state.current_company:
        st.info(f"📊 Currently analyzing: **{st.session_state.current_company}**")
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.write(message["content"])
            else:
                if "memo" in message:
                    st.markdown(message["memo"])
                else:
                    st.write(message["content"])
    
    # Main input area
    st.markdown("---")
    
    # File upload and text input in one section
    col1, col2 = st.columns([1, 3])
    
    with col1:
        uploaded_file = st.file_uploader(
            "📄 Upload Pitch Deck (Optional)",
            type=['pdf'],
            help="Upload a PDF pitch deck for analysis"
        )
    
    with col2:
        user_input = st.text_input(
            "💬 Ask me anything...",
            placeholder="e.g., 'Analyze Uber', 'What's Tesla's business model?', 'Research OpenAI'",
            key="user_input"
        )
    
    # Process button
    if st.button("🚀 Process", type="primary", use_container_width=True):
        if uploaded_file:
            # Process pitch deck
            doc, memo = process_pitch_deck(uploaded_file)
            if doc and memo:
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": f"Uploaded pitch deck: {uploaded_file.name}"
                })
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": "Investment memo generated from pitch deck:",
                    "memo": memo
                })
                st.success("✅ Pitch deck analyzed successfully!")
                st.rerun()
        
        elif user_input:
            # Process text input
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_input
            })
            
            # Extract company name
            company_name = extract_company_name(user_input)
            
            if company_name:
                # Analyze company
                doc, memo = handle_company_analysis(company_name)
                if doc and memo:
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": f"Investment memo generated for {company_name}:",
                        "memo": memo
                    })
                    st.success(f"✅ Analysis complete for {company_name}!")
                    st.rerun()
            else:
                # Handle general questions
                if st.session_state.current_company:
                    response = handle_question(user_input, st.session_state.current_company)
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": response
                    })
                    st.rerun()
                else:
                    st.error("Please specify a company name or upload a pitch deck first.")
                    st.rerun()
        else:
            st.warning("Please upload a file or enter a question.")
            st.rerun()
    
    # Quick actions
    if st.session_state.current_company:
        st.markdown("---")
        st.markdown("**Quick Actions:**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Show Memo", use_container_width=True):
                if st.session_state.current_memo:
                    st.markdown(st.session_state.current_memo)
        
        with col2:
            if st.button("📥 Download PDF", use_container_width=True):
                if st.session_state.current_memo:
                    pdf_bytes = generate_pdf_bytes(st.session_state.current_memo)
                    st.download_button(
                        label="Download Investment Memo",
                        data=pdf_bytes,
                        file_name=f"{st.session_state.current_company}_investment_memo.pdf",
                        mime="application/pdf"
                    )
        
        with col3:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.chat_history = []
                st.session_state.current_company = None
                st.session_state.current_memo = None
                st.session_state.current_doc = None
                st.rerun()
    
    # Instructions
    st.markdown("---")
    st.markdown("""
    **💡 How to use:**
    - **Upload a pitch deck** and I'll analyze it automatically
    - **Ask me to analyze a company** (e.g., "Analyze Tesla")
    - **Ask specific questions** about the analyzed company
    - **Research companies** without pitch decks using web data
    
    **🎯 Examples:**
    - "Analyze Uber's business model"
    - "What's Tesla's traction?"
    - "Research OpenAI's team"
    - "Show me Stripe's competitors"
    """)

if __name__ == "__main__":
    main() 