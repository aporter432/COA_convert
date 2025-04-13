from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER


def create_sample_coa(output_file="sample_coa.pdf"):
    """Create a sample Certificate of Analysis PDF file for testing."""
    doc = SimpleDocTemplate(output_file, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        name='TitleStyle',
        parent=styles['Normal'],
        fontSize=14,
        alignment=TA_CENTER,
        spaceAfter=12
    )
    
    header_style = ParagraphStyle(
        name='HeaderStyle',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_LEFT,
        spaceAfter=6
    )
    
    normal_style = styles["Normal"]
    
    # Content elements
    elements = []
    
    # Title
    elements.append(Paragraph("Certificate of Analysis", title_style))
    elements.append(Spacer(1, 12))
    
    # Metadata
    metadata = [
        ["Material:", "D14924998 NEOPRENE GNA M2 CHP 100 ABAG25KG"],
        ["Our/Customer Reference No:", "S030068A"]
    ]
    
    metadata_table = Table(metadata, colWidths=[150, 350])
    metadata_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    
    elements.append(metadata_table)
    elements.append(Spacer(1, 12))
    
    # Batch Information
    batch_info = [
        ["Batch", ""],
        ["241226D257", ""],
        ["Qty / Uom", ""],
        ["2,205.000 /LB", ""]
    ]
    
    batch_table = Table(batch_info, colWidths=[150, 350])
    batch_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
    ]))
    
    elements.append(batch_table)
    elements.append(Spacer(1, 20))
    
    # Test Results table
    elements.append(Paragraph("Test Results", header_style))
    elements.append(Spacer(1, 6))
    
    test_data = [
        ["Test Name", "Test Method", "Unit", "Value", "Specification"],
        ["s'TPOINT90", "N200.7405", "dNm", "11.73", "7.50 - 12.50"],
        ["TIME SCORCH01", "N200.7405", "min.", "2.47", "1.60 - 3.60"],
        ["VOLATILE", "N200.9500", "%", "1.50", "= < 1.30"],
        ["TIME TPOINT90", "N200.7405", "min.", "4.84", "2.10 - 7.60"],
        ["ML100", "N200.5700", "", "53", "47 - 59"],
        ["ML120", "N200.7460", "min.", "9.04", "= > 11.00"],
        ["DATE OF PRODUCTION", "", "", "20241229", ""],
        ["COUNTRY OF ORIGIN", "", "", "US", ""]
    ]
    
    test_table = Table(test_data, colWidths=[120, 80, 60, 80, 120])
    test_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    
    elements.append(test_table)
    
    # Build the document
    doc.build(elements)
    print(f"Sample COA PDF created: {output_file}")


if __name__ == "__main__":
    create_sample_coa() 