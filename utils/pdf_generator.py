import os
from datetime import date
import markdown2
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from io import BytesIO

def generate_pdf_bytes(memo_markdown: str, custom_css: str = None, chart_paths: dict = None) -> bytes:
    """
    Convert a markdown memo to PDF bytes for download.
    Returns PDF bytes instead of saving to file.
    """
    # Create a BytesIO buffer to store PDF
    buffer = BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, 
                           topMargin=72, bottomMargin=18)
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        textColor=colors.darkblue
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.darkblue
    )
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6
    )
    
    # Build story (content)
    story = []
    
    # Add title page
    today = date.today().strftime('%B %d, %Y')
    story.append(Paragraph("Investment Memo", title_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Generated on {today}", normal_style))
    story.append(PageBreak())
    
    # Convert markdown to simple text (basic conversion)
    lines = memo_markdown.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Handle headers
        if line.startswith('# '):
            story.append(Paragraph(line[2:], title_style))
            story.append(Spacer(1, 12))
        elif line.startswith('## '):
            story.append(Paragraph(line[3:], heading_style))
            story.append(Spacer(1, 6))
        elif line.startswith('### '):
            story.append(Paragraph(line[4:], heading_style))
            story.append(Spacer(1, 6))
        elif line.startswith('- ') or line.startswith('* '):
            # Handle bullet points
            bullet_text = line[2:]
            story.append(Paragraph(f"• {bullet_text}", normal_style))
        elif line.startswith('**') and line.endswith('**'):
            # Handle bold text
            bold_text = line[2:-2]
            bold_style = ParagraphStyle(
                'Bold',
                parent=normal_style,
                fontName='Helvetica-Bold'
            )
            story.append(Paragraph(bold_text, bold_style))
        else:
            # Regular text
            if line:
                story.append(Paragraph(line, normal_style))
    
    # Build PDF
    doc.build(story)
    
    # Get PDF bytes
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes

def generate_pdf(memo_markdown: str, output_path: str, custom_css: str = None, chart_paths: dict = None) -> None:
    """
    Convert a markdown memo to a styled PDF and save to output_path.
    Uses reportlab for PDF generation.
    """
    # Create PDF document
    doc = SimpleDocTemplate(output_path, pagesize=letter, rightMargin=72, leftMargin=72, 
                           topMargin=72, bottomMargin=18)
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        textColor=colors.darkblue
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.darkblue
    )
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6
    )
    
    # Build story (content)
    story = []
    
    # Add title page
    today = date.today().strftime('%B %d, %Y')
    story.append(Paragraph("Investment Memo", title_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Generated on {today}", normal_style))
    story.append(PageBreak())
    
    # Convert markdown to simple text (basic conversion)
    lines = memo_markdown.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Handle headers
        if line.startswith('# '):
            story.append(Paragraph(line[2:], title_style))
            story.append(Spacer(1, 12))
        elif line.startswith('## '):
            story.append(Paragraph(line[3:], heading_style))
            story.append(Spacer(1, 6))
        elif line.startswith('### '):
            story.append(Paragraph(line[4:], heading_style))
            story.append(Spacer(1, 6))
        elif line.startswith('- ') or line.startswith('* '):
            # Handle bullet points
            bullet_text = line[2:]
            story.append(Paragraph(f"• {bullet_text}", normal_style))
        elif line.startswith('**') and line.endswith('**'):
            # Handle bold text
            bold_text = line[2:-2]
            bold_style = ParagraphStyle(
                'Bold',
                parent=normal_style,
                fontName='Helvetica-Bold'
            )
            story.append(Paragraph(bold_text, bold_style))
        else:
            # Regular text
            if line:
                story.append(Paragraph(line, normal_style))
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Build PDF
    doc.build(story)

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