import os
from datetime import date
import markdown2
from weasyprint import HTML, CSS

def generate_pdf_bytes(memo_markdown: str, custom_css: str = None, chart_paths: dict = None) -> bytes:
    """
    Convert a markdown memo to PDF bytes for download.
    Returns PDF bytes instead of saving to file.
    """
    # Convert markdown to HTML
    html = markdown2.markdown(memo_markdown)

    # Add a cover page with timestamp
    today = date.today().strftime('%B %d, %Y')
    cover_html = f"""
    <div style='text-align:center; margin-top:100px;'>
        <h1>Investment Memo</h1>
        <p style='font-size:1.2em; color:#555;'>Generated on {today}</p>
    </div>
    <hr style='margin:40px 0;'>
    """

    # Embed charts if provided
    chart_html = ""
    if chart_paths:
        chart_html = "<div style='margin: 20px 0;'>"
        for chart_type, chart_path in chart_paths.items():
            if os.path.exists(chart_path):
                chart_title = chart_type.replace('_', ' ').title()
                chart_html += f"""
                <div style='margin: 30px 0; text-align: center;'>
                    <h3 style='color: #2E86AB; margin-bottom: 15px;'>{chart_title}</h3>
                    <img src='{chart_path}' style='width: 100%; max-width: 800px; height: auto;
                         border: 1px solid #ddd; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);' />
                </div>
                """
        chart_html += "</div>"

    full_html = f"""
    <html>
    <head>
        <meta charset='utf-8'>
        <title>Investment Memo</title>
    </head>
    <body>
        {cover_html}
        {html}
        {chart_html}
    </body>
    </html>
    """

    # Default CSS for clean, readable layout
    default_css = """
    @page { margin: 1in; }
    body { font-family: 'Inter', 'Arial', sans-serif; font-size: 12pt; color: #222; }
    h1, h2, h3, h4 { font-family: 'Inter', 'Arial', sans-serif; color: #1a1a1a; margin-top: 1.5em; }
    h1 { font-size: 2em; border-bottom: 2px solid #eee; padding-bottom: 0.2em; }
    h2 { font-size: 1.5em; border-bottom: 1px solid #eee; padding-bottom: 0.1em; }
    h3 { font-size: 1.2em; }
    ul, ol { margin-left: 1.5em; }
    li { margin-bottom: 0.3em; }
    blockquote { color: #555; border-left: 3px solid #eee; margin: 1em 0; padding-left: 1em; }
    code, pre { font-family: 'Fira Mono', 'Consolas', monospace; background: #f8f8f8; }
    table { border-collapse: collapse; width: 100%; margin: 1em 0; }
    th, td { border: 1px solid #ddd; padding: 0.5em; }
    th { background: #f5f5f5; }
    hr { border: none; border-top: 1px solid #eee; margin: 2em 0; }
    img { max-width: 100%; height: auto; }
    """
    css = CSS(string=custom_css or default_css)

    # Generate PDF and return bytes
    pdf_bytes = HTML(string=full_html).write_pdf(stylesheets=[css])
    return pdf_bytes

def generate_pdf(memo_markdown: str, output_path: str, custom_css: str = None, chart_paths: dict = None) -> None:
    """
    Convert a markdown memo to a styled PDF and save to output_path.
    - Adds a cover page with a timestamp.
    - Uses WeasyPrint for PDF generation.
    - Applies default or custom CSS for clean layout.
    - Embeds charts if provided.
    """
    # Convert markdown to HTML
    html = markdown2.markdown(memo_markdown)

    # Add a cover page with timestamp
    today = date.today().strftime('%B %d, %Y')
    cover_html = f"""
    <div style='text-align:center; margin-top:100px;'>
        <h1>Investment Memo</h1>
        <p style='font-size:1.2em; color:#555;'>Generated on {today}</p>
    </div>
    <hr style='margin:40px 0;'>
    """

    # Embed charts if provided
    chart_html = ""
    if chart_paths:
        chart_html = "<div style='margin: 20px 0;'>"
        for chart_type, chart_path in chart_paths.items():
            if os.path.exists(chart_path):
                chart_title = chart_type.replace('_', ' ').title()
                chart_html += f"""
                <div style='margin: 30px 0; text-align: center;'>
                    <h3 style='color: #2E86AB; margin-bottom: 15px;'>{chart_title}</h3>
                    <img src='{chart_path}' style='width: 100%; max-width: 800px; height: auto;
                         border: 1px solid #ddd; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);' />
                </div>
                """
        chart_html += "</div>"

    full_html = f"""
    <html>
    <head>
        <meta charset='utf-8'>
        <title>Investment Memo</title>
    </head>
    <body>
        {cover_html}
        {html}
        {chart_html}
    </body>
    </html>
    """

    # Default CSS for clean, readable layout
    default_css = """
    @page { margin: 1in; }
    body { font-family: 'Inter', 'Arial', sans-serif; font-size: 12pt; color: #222; }
    h1, h2, h3, h4 { font-family: 'Inter', 'Arial', sans-serif; color: #1a1a1a; margin-top: 1.5em; }
    h1 { font-size: 2em; border-bottom: 2px solid #eee; padding-bottom: 0.2em; }
    h2 { font-size: 1.5em; border-bottom: 1px solid #eee; padding-bottom: 0.1em; }
    h3 { font-size: 1.2em; }
    ul, ol { margin-left: 1.5em; }
    li { margin-bottom: 0.3em; }
    blockquote { color: #555; border-left: 3px solid #eee; margin: 1em 0; padding-left: 1em; }
    code, pre { font-family: 'Fira Mono', 'Consolas', monospace; background: #f8f8f8; }
    table { border-collapse: collapse; width: 100%; margin: 1em 0; }
    th, td { border: 1px solid #ddd; padding: 0.5em; }
    th { background: #f5f5f5; }
    hr { border: none; border-top: 1px solid #eee; margin: 2em 0; }
    img { max-width: 100%; height: auto; }
    """
    css = CSS(string=custom_css or default_css)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Generate PDF
    HTML(string=full_html).write_pdf(output_path, stylesheets=[css])

def generate_pdf_with_charts(memo_markdown: str, output_path: str, structured_doc, company_name: str) -> None:
    """
    Generate PDF with embedded charts from structured document data.

    Args:
        memo_markdown: The memo markdown content
        output_path: Where to save the PDF
        structured_doc: StructuredCompanyDoc object
        company_name: Name of the company
    """
    from utils.chart_generator import generate_charts_for_memo

    # Generate charts
    chart_paths = generate_charts_for_memo(company_name, structured_doc)

    # Generate PDF with charts
    generate_pdf(memo_markdown, output_path, chart_paths=chart_paths) 