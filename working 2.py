import streamlit as st
import pandas as pd
from datetime import datetime
import io
import re
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.platypus import HRFlowable

st.set_page_config(layout="wide", page_title="Clarius Pharma - Invoice")

# ─── SELLER ───────────────────────────────────────────────────────────────────
SELLER = """M/s CLARIUS PHARMA.
D.NO.19-1-358/4A. LECTURERS COLONY.
SRI RAMASAI NILAYAM PEDDAPURAM - 533437.
DL NO'S : 20B-AP/04/06/2017-137922.
21B-AP/04/06/2017-137923
GSTIN - 37AKYPB8654K1ZB"""

# ─── BUYERS ───────────────────────────────────────────────────────────────────
BUYERS = {
    "Mahalaxmi":        "TO, MAHALAXMI MEDICALS. RAMAMAHAL LADIES GATE ROAD. R.R. PET. ELURU-2.\nGSTIN NO- 37AJDPK5246N1ZT.\nD L NO- 339/AP/WG/E2011/R",
    "Balaji":           "TO, M/s BALAJI M/G/S. TADEPALLIGUDEM\nGSTIN NO-37BOPPP4153R1ZX.\n20&21-AP/05/2015-125403;125404",
    "Ramaswamy":        "TO: RAMASWAMY MEDICALS\nC/O DR. POTUMUDI SRINIWAS\nNEAR SUBBAMMADEVI SCHOOL, ELURU-2\nPH: 8008143357\nGSTIN: 37ASHPM3995K1ZZ\nDL NO: 140457-AP/05/01/2017 / 140458-AP/05/01/2017",
    "Laxmi Medicals":   "TO M/s LAXMI MEDICALS RETAIL SHOP,\nRAMARAOPET, KAKINADA.\nGSTIN-37ABIPV1833D1ZM.",
    "Manikanta":        "TO M/S SRI MANIKANTA MEDICALS.\nKOTHA ROAD, ELURU.\nD L NO: 54 54\nGSTIN: 37ACPPD6515N1Z5",
    "Madhura":          "TO, MADHURA MEDICALS YELESWARAM.\nGSTIN NO-37ABEFM6531H1Z7.\n20&21-985/AP/EG/R/2010/R",
    "Datta Sai Medicals": "TO, SRI DATTA SAI MEDICAL STORES.\nR.R.PETA, ELURU.\nDL.NO: 140/AP/WG/E/2009/R\nGSTIN: 37BRAPP1812M1ZO",
}

# ─── STYLES ───────────────────────────────────────────────────────────────────
def make_styles():
    ps = lambda name, **kw: ParagraphStyle(name, **kw)
    return {
        "seller": ps("seller", fontName="Helvetica-Bold", fontSize=7.5, leading=10, spaceAfter=0),
        "buyer":  ps("buyer",  fontName="Helvetica-Bold", fontSize=7.5, leading=10, spaceAfter=0),
        "info":   ps("info",   fontName="Helvetica", fontSize=7, leading=9, spaceAfter=0, alignment=TA_RIGHT),
        "hdr":    ps("hdr",    fontName="Helvetica-Bold", fontSize=6, leading=7, spaceAfter=0, alignment=TA_CENTER),
        "cell":   ps("cell",   fontName="Helvetica", fontSize=6.5, leading=8, spaceAfter=0, alignment=TA_CENTER),
        "cellL":  ps("cellL",  fontName="Helvetica", fontSize=6.5, leading=8, spaceAfter=0),
        "title":  ps("title",  fontName="Helvetica-Bold", fontSize=11, leading=14, spaceAfter=2, alignment=TA_CENTER),
        "sumL":   ps("sumL",   fontName="Helvetica", fontSize=7, leading=9, spaceAfter=0),
        "sumR":   ps("sumR",   fontName="Helvetica", fontSize=7, leading=9, spaceAfter=0, alignment=TA_RIGHT),
        "sumB":   ps("sumB",   fontName="Helvetica-Bold", fontSize=7, leading=9, spaceAfter=0, alignment=TA_RIGHT),
    }

# ─── COLOUR PALETTE ───────────────────────────────────────────────────────────
HDR_BG  = colors.HexColor("#1a3c6e")   # dark navy
HDR_FG  = colors.white
ROW_ALT = colors.HexColor("#eef3fb")   # very light blue
ROW_NRM = colors.white
SUM_BG  = colors.HexColor("#f0f4fc")
BORDER  = colors.HexColor("#8faad4")

# ─── PDF GENERATOR ────────────────────────────────────────────────────────────
def num(v, dec=2):
    if v == 0:
        return "-"
    return f"{v:,.{dec}f}"

def create_pdf(df, buyer_key, buyer_text, inv_no, date_val, transport, lr_no, lr_date):
    buf = io.BytesIO()
    PW, PH = landscape(A4)
    M = 12 * mm

    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        leftMargin=M, rightMargin=M,
        topMargin=10*mm, bottomMargin=10*mm,
    )
    W = PW - 2*M

    ST = make_styles()
    story = []

    # ── TITLE ────────────────────────────────────────────────────────────────
    story.append(Paragraph("GST INVOICE", ST["title"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=HDR_BG, spaceAfter=4))

    # ── HEADER TABLE (Seller | Buyer | Info) ─────────────────────────────────
    seller_para = Paragraph(SELLER.replace("\n", "<br/>"), ST["seller"])
    buyer_para  = Paragraph(buyer_text.replace("\n", "<br/>"), ST["buyer"])
    info_lines  = (
        f"<b>Inv No:</b> {inv_no}<br/>"
        f"<b>Date:</b>   {date_val}<br/>"
        f"<b>Transport:</b> {transport}<br/>"
        f"<b>Lr No:</b>  {lr_no}<br/>"
        f"<b>Lr Date:</b>{lr_date}"
    )
    info_para = Paragraph(info_lines, ST["info"])

    hdr_tbl = Table(
        [[seller_para, buyer_para, info_para]],
        colWidths=[W*0.28, W*0.45, W*0.27],
    )
    hdr_tbl.setStyle(TableStyle([
        ("BOX",        (0,0), (-1,-1), 0.8, BORDER),
        ("INNERGRID",  (0,0), (-1,-1), 0.5, BORDER),
        ("VALIGN",     (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING",(0,0), (-1,-1), 5),
        ("RIGHTPADDING",(0,0),(-1,-1), 5),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",(0,0),(-1,-1),4),
        ("BACKGROUND", (0,0), (-1,-1), ROW_ALT),
    ]))
    story.append(hdr_tbl)
    story.append(Spacer(1, 4))

    # ── PRODUCTS TABLE ───────────────────────────────────────────────────────
    def H(txt): return Paragraph(txt, ST["hdr"])
    def C(txt): return Paragraph(str(txt), ST["cell"])
    def CL(txt): return Paragraph(str(txt), ST["cellL"])

    headers = [
        H("#"), H("PRODUCT NAME"), H("PACKING"), H("HSN"), H("BATCH"), H("EXP"),
        H("QTY"), H("FREE"), H("PTR"), H("DISC"), H("MRP"), H("TAXABLE"),
        H("CGST\n%"), H("CGST\nAMT"), H("SGST\n%"), H("SGST\nAMT"), H("TOTAL"),
    ]

    cw_raw = [4, 18, 7, 7, 8, 5, 5, 5, 7, 6, 7, 8, 5, 6, 5, 6, 8]
    total_units = sum(cw_raw)
    col_widths  = [W * u / total_units for u in cw_raw]

    rows = [headers]
    for i, row in df.iterrows():
        rows.append([
            C(i+1),
            CL(row["Product"]),
            C(row["Packing"]),
            C(row["HSN"]),
            C(row["Batch"]),
            C(row["EXP"]),
            C(num(row["Qty"], 0)),
            C(num(row["Free"], 0)),
            C(num(row["PTR"])),
            C(num(row["Discount"])),
            C(num(row["MRP"])),
            C(num(row["Taxable"])),
            C(num(row["CGST%"], 0)),
            C(num(row["CGST Amt"])),
            C(num(row["SGST%"], 0)),
            C(num(row["SGST Amt"])),
            C(num(row["Total"])),
        ])

    # Pad to at least 8 data rows for aesthetics
    while len(rows) < 9:
        rows.append([C("") for _ in range(17)])

    prod_tbl = Table(rows, colWidths=col_widths, repeatRows=1)
    n = len(rows)
    ts = TableStyle([
        # Header row
        ("BACKGROUND",    (0,0), (-1,0),  HDR_BG),
        ("TEXTCOLOR",     (0,0), (-1,0),  HDR_FG),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,0),  6),
        ("ALIGN",         (0,0), (-1,0),  "CENTER"),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        # Alternating rows
        *[("BACKGROUND",  (0,r), (-1,r), ROW_ALT if r%2==0 else ROW_NRM)
          for r in range(1, n)],
        # Grid
        ("BOX",           (0,0), (-1,-1), 0.8, BORDER),
        ("INNERGRID",     (0,0), (-1,-1), 0.3, BORDER),
        # Padding
        ("TOPPADDING",    (0,0), (-1,-1), 2),
        ("BOTTOMPADDING", (0,0), (-1,-1), 2),
        ("LEFTPADDING",   (0,0), (-1,-1), 2),
        ("RIGHTPADDING",  (0,0), (-1,-1), 2),
    ])
    prod_tbl.setStyle(ts)
    story.append(prod_tbl)
    story.append(Spacer(1, 5))

    # ── SUMMARY SECTION ──────────────────────────────────────────────────────
    subtotal = df["Taxable"].sum()
    cgst_tot = df["CGST Amt"].sum()
    sgst_tot = df["SGST Amt"].sum()
    gst_tot  = cgst_tot + sgst_tot
    total_disc = (df["Qty"] * df["Discount"]).sum()
    net      = subtotal + gst_tot
    tot_items = len(df[df["Taxable"] > 0])
    tot_units = df["Qty"].sum()

    # GST breakdown
    gst_rates = [0, 5, 12, 18, 28]
    gst_summary = {}
    for _, row in df.iterrows():
        rate = int(row["CGST%"] + row["SGST%"])
        gst_summary.setdefault(rate, {"tax":0,"cgst":0,"sgst":0})
        gst_summary[rate]["tax"]  += row["Taxable"]
        gst_summary[rate]["cgst"] += row["CGST Amt"]
        gst_summary[rate]["sgst"] += row["SGST Amt"]

    def SL(t): return Paragraph(t, ST["sumL"])
    def SR(t): return Paragraph(t, ST["sumR"])
    def SB(t): return Paragraph(f"<b>{t}</b>", ST["sumB"])

    # Left: GST breakdown table
    gst_rows_data = [[
        Paragraph("<b>GST%</b>", ST["hdr"]),
        Paragraph("<b>TAX VALUE</b>", ST["hdr"]),
        Paragraph("<b>CGST AMT</b>", ST["hdr"]),
        Paragraph("<b>SGST VALUE</b>", ST["hdr"]),
        Paragraph("<b>SGST AMT</b>", ST["hdr"]),
    ]]
    for rate in gst_rates:
        d = gst_summary.get(rate, {"tax":0,"cgst":0,"sgst":0})
        gst_rows_data.append([
            SL(f"{rate}%"),
            SR(num(d["tax"])),
            SR(num(d["cgst"])),
            SR(num(d["tax"])),
            SR(num(d["sgst"])),
        ])

    gst_tbl = Table(gst_rows_data, colWidths=[W*0.06, W*0.1, W*0.09, W*0.1, W*0.09])
    gst_tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0), HDR_BG),
        ("TEXTCOLOR",    (0,0), (-1,0), HDR_FG),
        ("BOX",          (0,0), (-1,-1), 0.8, BORDER),
        ("INNERGRID",    (0,0), (-1,-1), 0.3, BORDER),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",   (0,0), (-1,-1), 2),
        ("BOTTOMPADDING",(0,0), (-1,-1), 2),
        ("LEFTPADDING",  (0,0), (-1,-1), 3),
        ("RIGHTPADDING", (0,0), (-1,-1), 3),
        *[("BACKGROUND", (0,r), (-1,r), ROW_ALT if r%2==0 else ROW_NRM)
          for r in range(1, len(gst_rows_data))],
    ]))

    # Middle: counts
    mid_data = [
        [SL("CASES:"), SR("")],
        [SL(f"No. of Items:"), SB(str(tot_items))],
        [SL(f"No. of Units:"), SB(num(tot_units, 0))],
        [SL("Due Date:"), SR("")],
        [SL("Note:"), SR("")],
    ]
    mid_tbl = Table(mid_data, colWidths=[W*0.1, W*0.08])
    mid_tbl.setStyle(TableStyle([
        ("BOX",          (0,0), (-1,-1), 0.8, BORDER),
        ("INNERGRID",    (0,0), (-1,-1), 0.3, BORDER),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ("BACKGROUND",   (0,0), (-1,-1), SUM_BG),
        ("TOPPADDING",   (0,0), (-1,-1), 2),
        ("BOTTOMPADDING",(0,0), (-1,-1), 2),
        ("LEFTPADDING",  (0,0), (-1,-1), 4),
        ("RIGHTPADDING", (0,0), (-1,-1), 4),
    ]))

    # Right: financial summary
    rnd = round(net) - net
    right_data = [
        [SL("SUB TOTAL"),  SB(f"₹ {num(subtotal)}")],
        [SL("LESS DISC"),  SR(f"₹ {num(total_disc)}")],
        [SL("GST AMT"),    SR(f"₹ {num(gst_tot)}")],
        [SL("ROUNDING"),   SR(f"₹ {num(rnd)}")],
        [SL("CR AMT"),     SR("₹ 0.00")],
        [Paragraph("<b>NET PAYABLE</b>", ST["sumB"]),
         Paragraph(f"<b>₹ {num(round(net))}</b>", ST["sumB"])],
    ]
    right_tbl = Table(right_data, colWidths=[W*0.13, W*0.13])
    right_tbl.setStyle(TableStyle([
        ("BOX",          (0,0), (-1,-1), 0.8, BORDER),
        ("INNERGRID",    (0,0), (-1,-1), 0.3, BORDER),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ("BACKGROUND",   (0,0), (-1,-1), SUM_BG),
        ("BACKGROUND",   (0,5), (-1,5), HDR_BG),
        ("TEXTCOLOR",    (0,5), (-1,5), HDR_FG),
        ("TOPPADDING",   (0,0), (-1,-1), 3),
        ("BOTTOMPADDING",(0,0), (-1,-1), 3),
        ("LEFTPADDING",  (0,0), (-1,-1), 4),
        ("RIGHTPADDING", (0,0), (-1,-1), 4),
    ]))

    # Spacer column between sections
    sp = W * 0.02
    summary_outer = Table(
        [[gst_tbl, "", mid_tbl, "", right_tbl]],
        colWidths=[W*0.44, sp, W*0.18, sp, W*0.26],
    )
    summary_outer.setStyle(TableStyle([
        ("VALIGN",  (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING",  (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
    ]))
    story.append(summary_outer)

    # ── FOOTER ───────────────────────────────────────────────────────────────
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=0.8, color=BORDER))
    footer_data = [[
        Paragraph("Subject to PEDDAPURAM Jurisdiction", ST["sumL"]),
        Paragraph("Goods once sold will not be taken back", ST["sumL"]),
        Paragraph("For <b>CLARIUS PHARMA</b><br/>Authorised Signatory", ST["info"]),
    ]]
    footer_tbl = Table(footer_data, colWidths=[W*0.33, W*0.34, W*0.33])
    footer_tbl.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("TOPPADDING", (0,0), (-1,-1), 3),
    ]))
    story.append(footer_tbl)

    doc.build(story)
    return buf.getvalue()


# ─── UI ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 1rem; }
    div[data-testid="stTextInput"] input { font-size: 13px; }
</style>
""", unsafe_allow_html=True)

st.markdown("## 🧾 Clarius Pharma — Invoice Generator")

col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    st.text_area("FROM", SELLER, height=140)

with col2:
    buyer_key = st.selectbox("Select Buyer", list(BUYERS.keys()))
    st.text_area("TO", BUYERS[buyer_key], height=140)

with col3:
    today = datetime.today().strftime("%d.%m.%Y")
    inv_no    = st.text_input("Inv No")
    date_val  = st.text_input("Date", value=today)
    transport = st.text_input("Transport")
    lr_no     = st.text_input("Lr No")
    lr_date   = st.text_input("Lr Date")

st.divider()

num_products = st.selectbox("Number of Products", list(range(1, 11)))
products = []

for i in range(num_products):
    st.markdown(f"**Product {i+1}**")
    c1 = st.columns(6)
    pname   = c1[0].text_input(f"Product Name",  key=f"pn{i}")
    packing = c1[1].text_input(f"Packing",        key=f"pk{i}")
    hsn     = c1[2].text_input(f"HSN",            key=f"hs{i}")
    batch   = c1[3].text_input(f"Batch",          key=f"ba{i}")
    exp     = c1[4].text_input(f"EXP",            key=f"ex{i}")
    qty     = c1[5].number_input(f"QTY",  value=0.0, key=f"qt{i}")

    c2 = st.columns(6)
    free = c2[0].number_input(f"FREE",  value=0.0, key=f"fr{i}")
    ptr  = c2[1].number_input(f"PTR",   value=0.0, key=f"pr{i}")
    disc = c2[2].number_input(f"DISC",  value=0.0, key=f"di{i}")
    mrp  = c2[3].number_input(f"MRP",   value=0.0, key=f"mr{i}")
    cgst = c2[4].number_input(f"CGST%", value=0.0, key=f"cg{i}")
    sgst = c2[5].number_input(f"SGST%", value=0.0, key=f"sg{i}")

    taxable  = qty * (ptr - disc)
    cgst_amt = taxable * cgst / 100
    sgst_amt = taxable * sgst / 100
    total    = taxable + cgst_amt + sgst_amt

    products.append({
        "Product": pname, "Packing": packing, "HSN": hsn, "Batch": batch,
        "EXP": exp, "Qty": qty, "Free": free, "PTR": ptr, "Discount": disc,
        "MRP": mrp, "Taxable": taxable, "CGST%": cgst, "SGST%": sgst,
        "CGST Amt": cgst_amt, "SGST Amt": sgst_amt, "Total": total,
    })

df = pd.DataFrame(products)

st.divider()
if "pdf_file" not in st.session_state:
    st.session_state.pdf_file = None

valid = any(p["Taxable"] > 0 for p in products)

if st.button("📄 Generate Invoice PDF", disabled=not valid, type="primary"):
    st.session_state.pdf_file = create_pdf(
        df, buyer_key, BUYERS[buyer_key],
        inv_no, date_val, transport, lr_no, lr_date
    )

if st.session_state.pdf_file:
    fname = re.sub(r"[^a-zA-Z0-9]", "_", inv_no or "invoice") + ".pdf"
    st.success("✅ Invoice generated!")
    st.download_button(
        "⬇️ Download PDF Invoice",
        st.session_state.pdf_file,
        file_name=fname,
        mime="application/pdf",
    )