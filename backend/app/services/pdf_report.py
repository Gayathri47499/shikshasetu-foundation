from datetime import datetime, timezone
from fpdf import FPDF
from fpdf.enums import XPos, YPos


def _clean_latin1(text: str) -> str:
    """Replace Unicode punctuation/currency symbols unsupported by standard PDF core fonts."""
    return (
        text.replace("₹", "INR ")
        .replace("—", "-")
        .replace("–", "-")
        .replace("’", "'")
        .replace("“", '"')
        .replace("”", '"')
    )


def generate_impact_pdf(impact_data: dict, schools: list) -> bytes:
    """Generate a downloadable Foundation Impact & School Summary PDF report."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Header banner
    pdf.set_fill_color(255, 241, 245)
    pdf.rect(10, 10, 190, 26, "F")
    pdf.set_xy(15, 14)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(40, 49, 59)
    pdf.cell(
        0, 8, "ShikshaSetu Foundation - Social Impact & Intervention Report",
        new_x=XPos.LMARGIN, new_y=YPos.NEXT,
    )
    pdf.set_x(15)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(104, 116, 130)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    pdf.cell(
        0, 6, f"Student Success & Intervention Intelligence Platform | Generated: {generated_at}",
        new_x=XPos.LMARGIN, new_y=YPos.NEXT,
    )

    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(217, 121, 152)
    pdf.cell(0, 8, "1. Key Social Impact Indicators", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(40, 49, 59)

    for kpi in impact_data.get("kpis", []):
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(85, 6, _clean_latin1(kpi["name"]), border=1)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(45, 6, _clean_latin1(str(kpi["value"])), border=1)
        pdf.set_font("Helvetica", "I", 8)
        pdf.cell(60, 6, _clean_latin1(kpi["data_label"]), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(217, 121, 152)
    pdf.cell(0, 8, "2. School-Level Attendance Baseline (Dataset A1)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(40, 49, 59)

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(35, 6, "Code", border=1)
    pdf.cell(65, 6, "School Name", border=1)
    pdf.cell(45, 6, "Enrolled Students", border=1)
    pdf.cell(45, 6, "Avg Attendance", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "", 9)
    for sc in schools:
        pdf.cell(35, 6, _clean_latin1(sc.code), border=1)
        pdf.cell(65, 6, _clean_latin1(sc.name), border=1)
        pdf.cell(45, 6, str(sc.enrolled_students), border=1)
        pdf.cell(45, 6, f"{sc.baseline_attendance_pct:.0f}%", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(217, 121, 152)
    pdf.cell(0, 8, "3. Responsible AI & Evaluation Caveats", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(40, 49, 59)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 5, _clean_latin1(impact_data.get("causal_disclaimer", "")))
    pdf.ln(3)
    pdf.multi_cell(
        0,
        5,
        "Note: The 12 student profiles (ST001-ST012) are synthetic illustrative records provided for the Veltris Challenge A assessment and do not contain verified dropout outcome labels.",
    )

    return bytes(pdf.output())
