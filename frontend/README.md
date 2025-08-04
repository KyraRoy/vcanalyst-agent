# VC Analyst Agent

A powerful AI-powered investment memo generator that analyzes companies and creates comprehensive investment memos with actionable recommendations.

## Features

- **Company Analysis**: Deep analysis of any company using web research and AI
- **Investment Recommendations**: Brutal honesty based on Speed, Depth, Taste, and Influence
- **Comprehensive Memos**: 15-section investment memos with real insights
- **PDF Export**: Download memos as professional PDFs
- **ChatGPT-like Interface**: Simple, intuitive single-input interface

## Deployment

### Streamlit Cloud (Recommended)

1. **Fork/Clone this repository**
2. **Go to [share.streamlit.io](https://share.streamlit.io)**
3. **Connect your GitHub account**
4. **Select this repository**
5. **Set deployment path to: `frontend`**
6. **Add environment variables:**
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `SERPAPI_KEY`: (Optional) For enhanced web search

### Local Development

```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

## Environment Variables

Create a `.env` file in the root directory:

```env
OPENAI_API_KEY=your_openai_api_key_here
SERPAPI_KEY=your_serpapi_key_here  # Optional
```

## Usage

1. **Enter a company name** (e.g., "Uber", "Perplexity", "Meta")
2. **Click "Process"** to generate the investment memo
3. **Review the comprehensive analysis** with investment recommendations
4. **Download as PDF** for sharing

## Architecture

- **Enhanced Analyzer**: GPT-4 powered company analysis
- **Web Research**: Comprehensive data gathering
- **Memo Generator**: Professional investment memo creation
- **PDF Generator**: High-quality PDF export

## Support

For issues or questions, please check the logs or create an issue in the repository. 