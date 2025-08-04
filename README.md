# VC Analyst Agent

An evidence-based, source-backed investment memo generator that automates VC research by extracting real data from company websites and external sources.

## 🚀 Features

- **Evidence-Based Analysis**: No hallucinated content - only source-backed information
- **Multi-Source Data**: Company websites + Google search results
- **Clean Text Extraction**: Filters out UI noise and preserves meaningful content
- **Structured Output**: Pydantic models with citations and evidence tracking
- **Conditional Memos**: Only renders sections with actual content
- **Source Citations**: Every claim backed by URL citations

## 📋 Architecture

```
VC ANALYST AGENT/
├── agents/
│   ├── company_researcher.py    # Main research orchestrator
│   ├── market_mapper.py         # Market analysis
│   ├── founder_profiler.py      # Team/founder analysis
│   └── memo_generator.py        # Conditional memo generation
├── models/
│   └── schemas.py              # Pydantic data models
├── utils/
│   ├── web_scraper.py          # Robust website scraping
│   ├── nlp.py                  # NLP extraction patterns
│   └── google_search.py        # Google search integration
├── data/
│   ├── test_input.json         # Company input data
│   └── memos/                  # Generated memos
└── main_agent.py               # Main entry point
```

## 🛠️ Installation

1. **Install dependencies**:
   ```bash
   python3 -m pip install -r requirements.txt --break-system-packages
   ```

2. **Set up Google Search API** (optional):
   ```bash
   export SERPAPI_KEY='your_serpapi_key_here'
   ```

## 🚀 Usage

### Basic Usage

```bash
python3 main_agent.py
```

This will:
1. Load company data from `data/test_input.json`
2. Scrape the company website
3. Perform Google searches (if API key available)
4. Extract structured information
5. Generate an evidence-based memo
6. Save results to `data/memos/`

### Input Format

Edit `data/test_input.json`:
```json
{
    "company": "Company Name",
    "website": "https://company.com",
    "founder": "Founder Name"
}
```

### Output

- **Text Memo**: `data/memos/{Company}_investment_memo.txt`
- **Structured Data**: `data/memos/{Company}_structured_data.json`

## 🔍 How It Works

### 1. Website Scraping
- Scrapes homepage + subpages (`/about`, `/product`, `/pricing`, etc.)
- Uses trafilatura for clean text extraction
- Filters out UI noise (navigation, cookies, controls)

### 2. Google Search Integration
- Performs 7 targeted searches:
  - `{company} traction`
  - `{company} funding`
  - `{company} MAU`
  - `{company} team`
  - `{company} product`
  - `{company} pricing`
  - `{company} press release`
- Extracts content from top 3 results per query
- Rate limited (1.5s between queries)

### 3. NLP Extraction
- Regex patterns for traction metrics, business models, team info
- Combines website + Google search content
- Creates citations for every piece of information

### 4. Conditional Memo Generation
- Only renders sections with actual content
- Includes source citations for every claim
- Lists missing fields transparently

## 📊 Example Output

```markdown
# Notion Investment Memo
Prepared on Jul 28, 2025

## 1. Introduction
The AI workspace that works for you. One place where teams find every answer, automate the busywork, and get projects done.

**Sources:** [website](https://notion.so/)

## 4. Product
The AI workspace that works for you. One place where teams find every answer, automate the busywork, and get projects done

**Sources:** [website](https://notion.so/)

## Missing Information
The following sections could not be populated with evidence:
- problem, solution, team, funding, etc.
```

## 🧪 Testing

### Test Extraction Pipeline
```bash
python3 test_extraction.py
```

### Test Google Integration
```bash
python3 test_google_integration.py
```

## 🔧 Configuration

### Environment Variables
- `SERPAPI_KEY`: Google search API key (optional)

### Rate Limiting
- Website scraping: 1s between requests
- Google search: 1.5s between queries
- Retry logic: 3 attempts with exponential backoff

### Text Cleaning
- Filters paragraphs under 40 characters
- Removes 50+ junk phrases (cookies, navigation, etc.)
- Preserves business-relevant content

## 📈 Performance

### Current Results
- **Text Quality**: 100% UI noise filtered out
- **Evidence Tracking**: Every claim has citations
- **Content Relevance**: Only meaningful business content preserved
- **Transparency**: Clear missing fields tracking

### Sample Companies Tested
- **Figma**: 4 populated sections (intro, solution, product, business_model)
- **Airtable**: 4 populated sections (intro, product, business_model, traction)
- **Notion**: 4 populated sections (intro, product, business_model, traction)

## 🚀 Next Steps

1. **Add More Data Sources**: LinkedIn, news APIs, Crunchbase
2. **Improve NLP**: ML summarization, better entity extraction
3. **Expand Coverage**: More subpages, better content discovery
4. **Add Caching**: Avoid re-fetching same URLs
5. **Team Extraction**: Better founder/team information

## 🤝 Contributing

The system is designed to be modular and extensible:

- **Add new data sources**: Create new modules in `utils/`
- **Improve extraction**: Enhance patterns in `utils/nlp.py`
- **Add new memo sections**: Update `models/schemas.py` and `agents/memo_generator.py`

## 📄 License

This project is for educational and research purposes.
# Updated Mon Aug  4 22:23:25 IST 2025
