"""
PDF Service — Generates premium, enterprise-grade GST-compliant invoices.
Company: VIPS TECH | Redhills, Chennai - 52, Tamil Nadu, India
"""
import io
from datetime import date
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


# ── Color Palette ──────────────────────────────────────────
BRAND      = colors.HexColor("#0f172a")   # Deep navy
ACCENT     = colors.HexColor("#2563eb")   # Royal blue
LIGHT_BG   = colors.HexColor("#f8fafc")   # Soft grey
BORDER     = colors.HexColor("#e2e8f0")   # Light border
TEXT_DARK   = colors.HexColor("#1e293b")   # Near black
TEXT_MID    = colors.HexColor("#475569")   # Medium grey
TEXT_LIGHT  = colors.HexColor("#94a3b8")   # Muted grey
SUCCESS     = colors.HexColor("#059669")   # Green for totals
WHITE       = colors.white


def generate_invoice_pdf(invoice_data: dict) -> bytes:
    """
    Generate a premium GST-compliant PDF invoice.
    """
    buffer = io.BytesIO()
    company = invoice_data.get("company", {})

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"Invoice {invoice_data.get('invoice_number', '')}",
    )

    elements = []
    page_width = A4[0] - 36 * mm  # usable width

    # ─────────────────────────────────────────────────────────
    # STYLES
    # ─────────────────────────────────────────────────────────
    s_company = ParagraphStyle("company", fontSize=22, fontName="Helvetica-Bold",
                               textColor=BRAND, spaceAfter=10, leading=26)
    s_tagline = ParagraphStyle("tagline", fontSize=8, textColor=TEXT_LIGHT,
                                fontName="Helvetica", spaceAfter=1, leading=11)
    s_invoice_title = ParagraphStyle("inv_title", fontSize=26, fontName="Helvetica-Bold",
                                     textColor=BORDER, alignment=TA_RIGHT, leading=30)
    s_label = ParagraphStyle("label", fontSize=7.5, fontName="Helvetica-Bold",
                              textColor=TEXT_LIGHT, spaceAfter=2, leading=10)
    s_value = ParagraphStyle("value", fontSize=9.5, fontName="Helvetica-Bold",
                              textColor=TEXT_DARK, leading=14)
    s_value_right = ParagraphStyle("value_r", fontSize=9, fontName="Helvetica",
                                    textColor=TEXT_DARK, alignment=TA_RIGHT, leading=13)
    s_label_right = ParagraphStyle("label_r", fontSize=7.5, fontName="Helvetica-Bold",
                                    textColor=TEXT_LIGHT, alignment=TA_RIGHT, spaceAfter=2, leading=10)
    s_table_hdr = ParagraphStyle("tbl_hdr", fontSize=7.5, fontName="Helvetica-Bold",
                                  textColor=WHITE, leading=10)
    s_table_hdr_r = ParagraphStyle("tbl_hdr_r", fontSize=7.5, fontName="Helvetica-Bold",
                                    textColor=WHITE, alignment=TA_RIGHT, leading=10)
    s_cell = ParagraphStyle("cell", fontSize=8.5, fontName="Helvetica",
                             textColor=TEXT_DARK, leading=12)
    s_cell_r = ParagraphStyle("cell_r", fontSize=8.5, fontName="Helvetica",
                               textColor=TEXT_DARK, alignment=TA_RIGHT, leading=12)
    s_cell_bold = ParagraphStyle("cell_b", fontSize=8.5, fontName="Helvetica-Bold",
                                  textColor=TEXT_DARK, leading=12)
    s_total_label = ParagraphStyle("tot_l", fontSize=9, fontName="Helvetica",
                                    textColor=TEXT_MID, alignment=TA_RIGHT, leading=14)
    s_total_value = ParagraphStyle("tot_v", fontSize=9, fontName="Helvetica-Bold",
                                    textColor=TEXT_DARK, alignment=TA_RIGHT, leading=14)
    s_grand_label = ParagraphStyle("gr_l", fontSize=12, fontName="Helvetica-Bold",
                                    textColor=BRAND, alignment=TA_RIGHT, leading=16)
    s_grand_value = ParagraphStyle("gr_v", fontSize=14, fontName="Helvetica-Bold",
                                    textColor=BRAND, alignment=TA_RIGHT, leading=18)
    s_footer = ParagraphStyle("footer", fontSize=7, textColor=TEXT_LIGHT,
                               alignment=TA_CENTER, leading=10)

    # ─────────────────────────────────────────────────────────
    # 1. HEADER — Company branding + Invoice title
    # ─────────────────────────────────────────────────────────
    company_name = company.get("name", "VIPS TECH")
    company_addr = company.get("address", "Redhills, Chennai - 52")
    company_city = company.get("city", "Chennai")
    company_state = company.get("state", "Tamil Nadu")
    company_pin = company.get("pincode", "600052")
    company_gst = company.get("gst_number", "ST5467F")
    company_phone = company.get("phone", "7695924565")
    company_email = company.get("email", "[EMAIL_ADDRESS]")

    left_header = Paragraph(company_name, s_company)
    left_details = Paragraph(
        f"{company_addr}<br/>"
        f"{company_city}, {company_state} - {company_pin}<br/>"
        f"<b>Country:</b> India<br/>"
        + (f"<b>GSTIN:</b> {company_gst}<br/>" if company_gst else "")
        + (f"Ph: {company_phone}" if company_phone else "")
        + (f" | {company_email}" if company_email else ""),
        s_tagline
    )
    right_title = Paragraph("INVOICE", s_invoice_title)

    header_table = Table(
        [[left_header, right_title],
         [left_details, ""]],
        colWidths=[page_width * 0.65, page_width * 0.35]
    )
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("VALIGN", (1, 0), (1, 0), "TOP"), # INVOICE label
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("SPAN", (1, 0), (1, 1)),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 4 * mm))

    # Accent line
    elements.append(Spacer(1, 3 * mm))
    elements.append(HRFlowable(width="100%", thickness=2, color=ACCENT))
    elements.append(Spacer(1, 8 * mm))

    # ─────────────────────────────────────────────────────────
    # 2. BILL TO / INVOICE DETAILS — Two-column layout
    # ─────────────────────────────────────────────────────────
    customer_name = invoice_data.get("customer_name")
    customer_company = invoice_data.get("customer_company")
    customer_store = invoice_data.get("customer_store")
    customer_gst = invoice_data.get("customer_gst", "")
    customer_addr = invoice_data.get("customer_address", "")
    inv_number = invoice_data.get("invoice_number", "")
    inv_date = invoice_data.get("invoice_date", date.today().isoformat())
    supply_type = invoice_data.get("supply_type", "intra")

    # Build the Bill To content dynamically
    bill_to_html = [f"<font size='7.5' color='#94a3b8'><b>BILL TO</b></font><br/>"]
    
    if customer_company:
        bill_to_html.append(f"<font size='11'><b>{customer_company}</b></font><br/>")
    
    if customer_store:
        bill_to_html.append(f"<font size='9'>{customer_store}</font><br/>")
        
    if customer_name and str(customer_name).lower() not in ("null", "none", "customer"):
        name_prefix = "Attn: " if customer_company or customer_store else ""
        bill_to_html.append(f"<font size='9.5'>{name_prefix}{customer_name}</font><br/>")
    
    # Fallback if no specific details found
    if not customer_company and not customer_store and (not customer_name or str(customer_name).lower() in ("null", "none", "customer")):
        bill_to_html.append(f"<font size='11'><b>Customer</b></font><br/>")

    if customer_addr:
        bill_to_html.append(f"<font size='8.5'>{customer_addr}</font><br/>")
    
    if customer_gst:
        bill_to_html.append(f"<font size='8' color='#475569'>GSTIN: {customer_gst}</font>")

    bill_left = Paragraph("".join(bill_to_html), s_value)

    bill_right = Paragraph(
        f"<font size='7.5' color='#94a3b8'><b>INVOICE NO</b></font><br/>"
        f"<font size='11'><b>{inv_number}</b></font><br/>"
        f"<font size='7.5' color='#94a3b8'><b>DATE</b></font><br/>"
        f"<font size='9'>{inv_date}</font><br/>"
        f"<font size='7.5' color='#94a3b8'><b>SUPPLY TYPE</b></font><br/>"
        f"<font size='9'>{supply_type.upper()}-STATE</font>",
        s_value_right
    )

    info_table = Table(
        [[bill_left, bill_right]],
        colWidths=[page_width * 0.55, page_width * 0.45]
    )
    info_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (0, 0), LIGHT_BG),
        ("LEFTPADDING", (0, 0), (0, 0), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 8 * mm))

    # ─────────────────────────────────────────────────────────
    # 3. LINE ITEMS TABLE
    # ─────────────────────────────────────────────────────────
    items = invoice_data.get("items", [])

    # Column headers
    col_headers = [
        Paragraph("#", s_table_hdr),
        Paragraph("PRODUCT / DESCRIPTION", s_table_hdr),
        Paragraph("HSN", s_table_hdr),
        Paragraph("QTY", s_table_hdr_r),
        Paragraph("RATE (₹)", s_table_hdr_r),
        Paragraph("GST %", s_table_hdr_r),
        Paragraph("TAX (₹)", s_table_hdr_r),
        Paragraph("AMOUNT (₹)", s_table_hdr_r),
    ]
    col_widths = [8*mm, 52*mm, 16*mm, 16*mm, 22*mm, 14*mm, 20*mm, 24*mm]

    rows = [col_headers]

    for i, item in enumerate(items, 1):
        row = [
            Paragraph(str(i), s_cell),
            Paragraph(f"<b>{item['product_name']}</b>", s_cell_bold),
            Paragraph(item.get("hsn_code") or "—", s_cell),
            Paragraph(f"{item['quantity']} {item.get('unit', 'pc')}", s_cell_r),
            Paragraph(f"₹{item['unit_price']:,.2f}", s_cell_r),
            Paragraph(f"{item['gst_rate']:.0f}%", s_cell_r),
            Paragraph(f"₹{item['gst_amount']:,.2f}", s_cell_r),
            Paragraph(f"₹{item['total_amount']:,.2f}", s_cell_r),
        ]
        rows.append(row)

    items_table = Table(rows, colWidths=col_widths, repeatRows=1)

    # Professional table styling
    table_style = [
        # Header row — dark navy background
        ("BACKGROUND", (0, 0), (-1, 0), BRAND),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("LEFTPADDING", (0, 0), (-1, 0), 6),
        ("RIGHTPADDING", (0, 0), (-1, 0), 6),

        # Data rows
        ("TOPPADDING", (0, 1), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 7),
        ("LEFTPADDING", (0, 1), (-1, -1), 6),
        ("RIGHTPADDING", (0, 1), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

        # Grid lines — subtle
        ("LINEBELOW", (0, 0), (-1, 0), 1.5, ACCENT),
        ("LINEBELOW", (0, 1), (-1, -2), 0.5, BORDER),
        ("LINEBELOW", (0, -1), (-1, -1), 1, BRAND),
    ]

    # Alternating row colors
    for idx in range(1, len(rows)):
        if idx % 2 == 0:
            table_style.append(("BACKGROUND", (0, idx), (-1, idx), LIGHT_BG))

    items_table.setStyle(TableStyle(table_style))
    elements.append(items_table)
    elements.append(Spacer(1, 6 * mm))

    # ─────────────────────────────────────────────────────────
    # 4. TOTALS SECTION — Right-aligned
    # ─────────────────────────────────────────────────────────
    subtotal = invoice_data.get("subtotal", 0)
    cgst = invoice_data.get("cgst_amount", 0)
    sgst = invoice_data.get("sgst_amount", 0)
    igst = invoice_data.get("igst_amount", 0)
    bonus = invoice_data.get("bonus", 0)
    total = invoice_data.get("total_amount", 0)

    totals_rows = [
        [Paragraph("Subtotal (Taxable)", s_total_label),
         Paragraph(f"₹{subtotal:,.2f}", s_total_value)],
    ]

    if supply_type == "inter":
        totals_rows.append([
            Paragraph("IGST", s_total_label),
            Paragraph(f"₹{igst:,.2f}", s_total_value)
        ])
    else:
        totals_rows.append([
            Paragraph("CGST", s_total_label),
            Paragraph(f"₹{cgst:,.2f}", s_total_value)
        ])
        totals_rows.append([
            Paragraph("SGST", s_total_label),
            Paragraph(f"₹{sgst:,.2f}", s_total_value)
        ])

    if bonus != 0:
        label = "Extra Adjustment" if bonus > 0 else "Discount"
        sign = "+" if bonus > 0 else "-"
        totals_rows.append([
            Paragraph(label, s_total_label),
            Paragraph(f"{sign}₹{abs(bonus):,.2f}", s_total_value)
        ])

    # Grand total row
    totals_rows.append([
        Paragraph("GRAND TOTAL", s_grand_label),
        Paragraph(f"₹{total:,.2f}", s_grand_value)
    ])

    totals_table = Table(totals_rows, colWidths=[35 * mm, 30 * mm])
    totals_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -2), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -2), 4),
        # Grand total highlight
        ("LINEABOVE", (0, -1), (-1, -1), 1.5, BRAND),
        ("TOPPADDING", (0, -1), (-1, -1), 8),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 8),
        ("BACKGROUND", (0, -1), (-1, -1), LIGHT_BG),
    ]))

    # Wrap in right-aligned container
    outer = Table([[Paragraph(""), totals_table]], colWidths=[page_width - 68 * mm, 68 * mm])
    outer.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    elements.append(outer)
    elements.append(Spacer(1, 12 * mm))

    # ─────────────────────────────────────────────────────────
    # 5. NOTES & BANK DETAILS
    # ─────────────────────────────────────────────────────────
    notes_style = ParagraphStyle("notes", fontSize=8, textColor=TEXT_MID,
                                  leading=12, fontName="Helvetica")
    notes_label = ParagraphStyle("notes_l", fontSize=7.5, textColor=TEXT_LIGHT,
                                  fontName="Helvetica-Bold", spaceAfter=3)

    elements.append(Paragraph("NOTES:", notes_label))
    elements.append(Paragraph(
        "Thank you for your business. Payment is due within 30 days.<br/>"
        "Please include the invoice number in your payment reference.",
        notes_style
    ))
    elements.append(Spacer(1, 10 * mm))

    # ─────────────────────────────────────────────────────────
    # 6. FOOTER
    # ─────────────────────────────────────────────────────────
    elements.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    elements.append(Spacer(1, 3 * mm))
    elements.append(Paragraph(
        f"This is a computer-generated invoice and does not require a signature. | "
        f"{company_name} | {company_addr}, {company_city}, {company_state}, India"
        + (f" | GSTIN: {company_gst}" if company_gst else "")
        + f" | Generated by VoiceInvoice",
        s_footer
    ))

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
