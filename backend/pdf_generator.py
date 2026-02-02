"""
PDF Generator for Firm Offers.
Creates professional PDF documents from offer data.
"""
import io
from datetime import datetime
from typing import Optional

# Try to import reportlab, fallback gracefully
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm, cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, HRFlowable
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def is_pdf_available() -> bool:
    """Check if PDF generation is available."""
    return REPORTLAB_AVAILABLE


def generate_offer_pdf(
    offer_text: str,
    load_port: str,
    discharge_port: str,
    cargo: str,
    quantity: int,
    freight_rate: float,
    demurrage_rate: float,
    laycan_start: str,
    laycan_end: str,
    charterer_name: Optional[str] = None,
    offer_id: Optional[int] = None,
    status: str = "draft"
) -> bytes:
    """
    Generate a PDF document from offer data.

    Returns:
        bytes: PDF file content
    """
    if not REPORTLAB_AVAILABLE:
        raise ImportError("reportlab is not installed. Install with: pip install reportlab")

    # Create buffer
    buffer = io.BytesIO()

    # Create document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    # Styles
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=12,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1a365d')
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=colors.grey
    )

    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=12,
        spaceBefore=15,
        spaceAfter=8,
        textColor=colors.HexColor('#2c5282'),
        borderColor=colors.HexColor('#e2e8f0'),
        borderWidth=1,
        borderPadding=5
    )

    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY,
        spaceAfter=6
    )

    clause_style = ParagraphStyle(
        'ClauseText',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        leftIndent=10,
        spaceAfter=4
    )

    # Build content
    story = []

    # Title
    story.append(Paragraph("FIRM OFFER", title_style))

    # Subtitle with metadata
    ref_text = f"Offer #{offer_id}" if offer_id else "Draft"
    date_text = datetime.now().strftime("%d %B %Y")
    story.append(Paragraph(f"{ref_text} | {date_text} | Status: {status.upper()}", subtitle_style))

    # Horizontal line
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e2e8f0')))
    story.append(Spacer(1, 10))

    # Summary table
    summary_data = [
        ["Route:", f"{load_port} → {discharge_port}"],
        ["Cargo:", f"{cargo} | {quantity:,} MT"],
        ["Freight:", f"USD {freight_rate:.2f} PMT FIOST"],
        ["Demurrage:", f"USD {demurrage_rate:,.0f} PDPR"],
        ["Laycan:", f"{laycan_start} to {laycan_end}"],
    ]

    if charterer_name:
        summary_data.insert(0, ["Charterer:", charterer_name])

    summary_table = Table(summary_data, colWidths=[3*cm, 12*cm])
    summary_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#4a5568')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(summary_table)

    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e2e8f0')))
    story.append(Spacer(1, 10))

    # Offer text - split by sections
    story.append(Paragraph("TERMS AND CONDITIONS", section_style))
    story.append(Spacer(1, 5))

    # Process offer text
    lines = offer_text.split('\n')
    current_section = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Skip headers we already displayed
        if line == "FIRM OFFER" or line.startswith("==="):
            continue

        # Section headers (lines with dashes)
        if line.startswith("---") or line.startswith("-" * 20):
            continue

        # Check if it's a section header
        if line.endswith(":") and len(line) < 50:
            story.append(Spacer(1, 8))
            story.append(Paragraph(line, section_style))
            current_section = line
            continue

        # Regular clause/text
        # Escape special characters for reportlab
        safe_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        story.append(Paragraph(safe_line, clause_style))

    # Footer
    story.append(Spacer(1, 30))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e0')))
    story.append(Spacer(1, 10))

    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    story.append(Paragraph(
        f"Generated by FrtOffersCopilot | {datetime.now().strftime('%Y-%m-%d %H:%M')} | "
        "This document is for information purposes only",
        footer_style
    ))

    # Build PDF
    doc.build(story)

    # Get PDF content
    pdf_content = buffer.getvalue()
    buffer.close()

    return pdf_content


def generate_simple_pdf(offer_text: str, title: str = "Firm Offer") -> bytes:
    """
    Generate a simple PDF with just the offer text.
    Simpler alternative when full formatting not needed.
    """
    if not REPORTLAB_AVAILABLE:
        raise ImportError("reportlab is not installed")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()

    story = []

    # Title
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=20,
        alignment=TA_CENTER
    )
    story.append(Paragraph(title, title_style))

    # Body
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        spaceAfter=6
    )

    for line in offer_text.split('\n'):
        if line.strip():
            safe_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            story.append(Paragraph(safe_line, body_style))
        else:
            story.append(Spacer(1, 6))

    doc.build(story)

    pdf_content = buffer.getvalue()
    buffer.close()

    return pdf_content
