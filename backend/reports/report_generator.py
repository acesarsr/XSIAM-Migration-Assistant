"""
Report Generator for XSIAM Migration Coverage Analysis
Generates CSV and PDF reports with statistics and recommendations
"""
import csv
from io import BytesIO, StringIO
from typing import List, Dict
from datetime import datetime

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.platypus import Image as RLImage
    from reportlab.graphics.shapes import Drawing
    from reportlab.graphics.charts.piecharts import Pie
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def generate_csv_report(rules: List[Dict], coverage_results: List[Dict]) -> StringIO:
    """
    Generate CSV coverage report
    
    Args:
        rules: List of rule dictionaries
        coverage_results: List of coverage analysis results
        
    Returns:
        StringIO buffer containing CSV data
    """
    csv_buffer = StringIO()
    writer = csv.writer(csv_buffer)
    
    # Header
    writer.writerow([
        'Rule ID',
        'Rule Name',
        'Source Platform',
        'Status',
        'Coverage',
        'Best Match',
        'Confidence',
        'Severity',
        'ATT&CK Tactics',
        'Original Query (Truncated)'
    ])
    
    # Data rows
    for rule, coverage in zip(rules, coverage_results):
        best_match = coverage.get('all_matches', [{}])[0] if coverage.get('all_matches') else {}
        
        writer.writerow([
            rule.get('id', ''),
            rule.get('name', ''),
            rule.get('source_platform', ''),
            rule.get('status', ''),
            'Yes' if coverage.get('covered') else 'No',
            coverage.get('best_match', 'N/A'),
            f"{int(coverage.get('confidence', 0) * 100)}%",
            best_match.get('severity', 'N/A'),
            best_match.get('tactics', 'N/A'),
            (rule.get('original_query', '')[:100] + '...') if len(rule.get('original_query', '')) > 100 else rule.get('original_query', '')
        ])
    
    # Summary statistics at the end
    writer.writerow([])
    writer.writerow(['=== SUMMARY STATISTICS ==='])
    writer.writerow(['Total Rules', len(rules)])
    covered_count = sum(1 for c in coverage_results if c.get('covered'))
    writer.writerow(['Covered by XSIAM Analytics', covered_count])
    writer.writerow(['Coverage Percentage', f"{(covered_count / len(rules) * 100) if rules else 0:.1f}%"])
    
    # Platform breakdown
    platforms = {}
    for rule in rules:
        platform = rule.get('source_platform', 'unknown')
        platforms[platform] = platforms.get(platform, 0) + 1
    
    writer.writerow([])
    writer.writerow(['Platform', 'Count'])
    for platform, count in platforms.items():
        writer.writerow([platform.capitalize(), count])
    
    csv_buffer.seek(0)
    return csv_buffer


def generate_pdf_report(rules: List[Dict], coverage_results: List[Dict]) -> BytesIO:
    """
    Generate PDF coverage report with charts and detailed analysis
    
    Args:
        rules: List of rule dictionaries
        coverage_results: List of coverage analysis results
        
    Returns:
        BytesIO buffer containing PDF data
    """
    if not REPORTLAB_AVAILABLE:
        # Fallback to simple text-based PDF
        pdf_buffer = BytesIO()
        pdf_buffer.write(b"PDF generation requires reportlab library. Install with: pip install reportlab")
        pdf_buffer.seek(0)
        return pdf_buffer
    
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=30,
        alignment=1  # Center
    )
    story.append(Paragraph("XSIAM Migration Coverage Analysis Report", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Metadata
    story.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Paragraph(f"<b>Total Rules Analyzed:</b> {len(rules)}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Executive Summary
    story.append(Paragraph("Executive Summary", styles['Heading2']))
    covered_count = sum(1 for c in coverage_results if c.get('covered'))
    coverage_pct = (covered_count / len(rules) * 100) if rules else 0
    
    summary_data = [
        ['Metric', 'Value'],
        ['Total Rules', str(len(rules))],
        ['Covered by XSIAM Analytics', str(covered_count)],
        ['Not Covered', str(len(rules) - covered_count)],
        ['Coverage Percentage', f'{coverage_pct:.1f}%']
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f1f5f9')),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Pie Chart - Coverage Breakdown
    if covered_count > 0 or (len(rules) - covered_count) > 0:
        drawing = Drawing(400, 200)
        pie = Pie()
        pie.x = 150
        pie.y = 50
        pie.width = 100
        pie.height = 100
        pie.data = [covered_count, len(rules) - covered_count]
        pie.labels = ['Covered', 'Not Covered']
        pie.slices.strokeWidth = 0.5
        pie.slices[0].fillColor = colors.HexColor('#10b981')
        pie.slices[1].fillColor = colors.HexColor('#ef4444')
        drawing.add(pie)
        story.append(drawing)
        story.append(Spacer(1, 0.3*inch))
    
    # Platform Breakdown
    story.append(Paragraph("Platform Breakdown", styles['Heading2']))
    platforms = {}
    for rule in rules:
        platform = rule.get('source_platform', 'unknown')
        platforms[platform] = platforms.get(platform, 0) + 1
    
    platform_data = [['Platform', 'Count']]
    for platform, count in platforms.items():
        platform_data.append([platform.capitalize(), str(count)])
    
    platform_table = Table(platform_data, colWidths=[3*inch, 2*inch])
    platform_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f1f5f9')),
    ]))
    story.append(platform_table)
    story.append(PageBreak())
    
    # Detailed Rule Analysis
    story.append(Paragraph("Detailed Rule Analysis", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))
    
    for idx, (rule, coverage) in enumerate(zip(rules[:20], coverage_results[:20]), 1):  # Limit to 20 for PDF size
        story.append(Paragraph(f"<b>{idx}. {rule.get('name', 'Unnamed Rule')}</b>", styles['Heading3']))
        
        details = [
            ['Property', 'Value'],
            ['Source Platform', rule.get('source_platform', '').capitalize()],
            ['Status', rule.get('status', '').capitalize()],
            ['Coverage', 'Yes ✓' if coverage.get('covered') else 'No ✗'],
        ]
        
        if coverage.get('covered'):
            details.append(['Best Match', coverage.get('best_match', 'N/A')])
            details.append(['Confidence', f"{int(coverage.get('confidence', 0) * 100)}%"])
        
        details_table = Table(details, colWidths=[2*inch, 4*inch])
        details_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#cbd5e1')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(details_table)
        story.append(Spacer(1, 0.2*inch))
    
    if len(rules) > 20:
        story.append(Paragraph(f"<i>... and {len(rules) - 20} more rules. See CSV report for full details.</i>", styles['Italic']))
    
    # Build PDF
    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer
