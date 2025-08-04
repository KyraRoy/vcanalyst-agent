#!/usr/bin/env python3
"""
Create a simple test PDF pitch deck for testing the parser.
"""

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import os

def create_test_pitch_deck():
    """Create a simple test pitch deck PDF"""
    
    # Create output directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Create the PDF
    doc = SimpleDocTemplate("data/sample_pitch_deck.pdf", pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title slide
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1  # Center
    )
    
    story.append(Paragraph("DesignTech", title_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph("AI-Powered Design Platform", styles['Heading2']))
    story.append(Spacer(1, 40))
    
    # Problem slide
    story.append(Paragraph("The Problem", styles['Heading1']))
    story.append(Spacer(1, 20))
    story.append(Paragraph("• Traditional design tools are too complex for non-designers", styles['Normal']))
    story.append(Paragraph("• High learning curve and expensive software", styles['Normal']))
    story.append(Paragraph("• Limited collaboration features", styles['Normal']))
    story.append(Paragraph("• 80% of users give up within first week", styles['Normal']))
    story.append(Spacer(1, 40))
    
    # Solution slide
    story.append(Paragraph("Our Solution", styles['Heading1']))
    story.append(Spacer(1, 20))
    story.append(Paragraph("• AI-powered design platform for everyone", styles['Normal']))
    story.append(Paragraph("• Drag-and-drop interface with smart suggestions", styles['Normal']))
    story.append(Paragraph("• Real-time collaboration and sharing", styles['Normal']))
    story.append(Paragraph("• 10x faster than traditional tools", styles['Normal']))
    story.append(Spacer(1, 40))
    
    # Market slide
    story.append(Paragraph("Market Opportunity", styles['Heading1']))
    story.append(Spacer(1, 20))
    story.append(Paragraph("• TAM: $50B global design software market", styles['Normal']))
    story.append(Paragraph("• SAM: $10B SMB design tools segment", styles['Normal']))
    story.append(Paragraph("• SOM: $2B our target market", styles['Normal']))
    story.append(Paragraph("• Growing 15% annually", styles['Normal']))
    story.append(Spacer(1, 40))
    
    # Traction slide
    story.append(Paragraph("Traction", styles['Heading1']))
    story.append(Spacer(1, 20))
    story.append(Paragraph("• 100K+ active users", styles['Normal']))
    story.append(Paragraph("• $2M ARR", styles['Normal']))
    story.append(Paragraph("• 300% YoY growth", styles['Normal']))
    story.append(Paragraph("• 4.8/5 user rating", styles['Normal']))
    story.append(Spacer(1, 40))
    
    # Team slide
    story.append(Paragraph("Team", styles['Heading1']))
    story.append(Spacer(1, 20))
    story.append(Paragraph("• CEO: Former design lead at Figma", styles['Normal']))
    story.append(Paragraph("• CTO: 10+ years in software development", styles['Normal']))
    story.append(Paragraph("• CPO: Ex-Google UX designer", styles['Normal']))
    story.append(Paragraph("• 15 total team members", styles['Normal']))
    story.append(Spacer(1, 40))
    
    # Funding slide
    story.append(Paragraph("Funding", styles['Heading1']))
    story.append(Spacer(1, 20))
    story.append(Paragraph("• Raising $5M Series A", styles['Normal']))
    story.append(Paragraph("• $25M pre-money valuation", styles['Normal']))
    story.append(Paragraph("• Use of funds: Product development & sales", styles['Normal']))
    story.append(Paragraph("• Previous: $1M seed from Y Combinator", styles['Normal']))
    
    # Build the PDF
    doc.build(story)
    print("✅ Test pitch deck created: data/sample_pitch_deck.pdf")

if __name__ == "__main__":
    create_test_pitch_deck() 