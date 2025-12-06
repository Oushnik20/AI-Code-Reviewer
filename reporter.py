import os, time, re
from fpdf import FPDF

# ---------- Helpers ----------
def find_font():
    """Try to find a Unicode TTF; return path or None."""
    win_fonts = r"C:\Windows\Fonts"
    candidates = [
        "arial.ttf", "arialuni.ttf", "segoeui.ttf", "calibri.ttf",
        "cambria.ttf", "consola.ttf", "times.ttf", "cour.ttf"
    ]
    for name in candidates:
        p = os.path.join(win_fonts, name)
        if os.path.exists(p):
            print(f"✅ Using font: {p}")
            return p
    print("⚠️ No system TTF font found — fallback Helvetica.")
    return None


def sanitize(text):
    """Convert any input to safe plain text (remove unsupported characters)."""
    if isinstance(text, list):
        text = "\n".join(str(x) for x in text)
    elif isinstance(text, dict):
        text = "\n".join(f"{k}: {v}" for k, v in text.items())
    elif not isinstance(text, str):
        text = str(text)
    # Strip unsupported Unicode (emojis, symbols) for fallback mode
    return re.sub(r"[^\x00-\xFF]", "", text or "")


def clamp(s: str, lim: int = 4000) -> str:
    """Limit length of long strings."""
    s = s or ""
    return s if len(s) <= lim else s[:lim] + "\n...[truncated]..."


# ---------- Core ----------
def _render_pdf(pdf: FPDF, repo_url: str, suggestions: list, full_output, unicode_mode: bool):
    """Render structured, readable AI analysis report with proper code suggestions."""

    def flatten_text(data):
        """Recursively flatten dicts/lists into readable string."""
        if isinstance(data, dict):
            return "\n".join(f"{k}: {flatten_text(v)}" for k, v in data.items())
        elif isinstance(data, list):
            return "\n".join(flatten_text(x) for x in data)
        return str(data or "")

    def extract_code_blocks(text):
        """Extract code blocks (```python ... ```)."""
        text = flatten_text(text)
        blocks = re.findall(r"```(?:python)?(.*?)```", text, re.DOTALL)
        return [b.strip() for b in blocks if b.strip()]

    # --- PDF setup ---
    title = "DevMate – AI Multi-Agent Code Review Report"
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Auto" if unicode_mode else "Helvetica", "B", 16)
    pdf.cell(0, 10, sanitize(title), ln=True, align="C")
    pdf.ln(6)

    # --- Meta Info ---
    pdf.set_font("Auto" if unicode_mode else "Helvetica", "", 12)
    meta = f"Repository: {repo_url}\nGenerated on: {time.strftime('%Y-%m-%d %H:%M:%S')}"
    pdf.multi_cell(0, 7, sanitize(meta))
    pdf.ln(4)

    # --- Structured Sections ---
    section_titles = {
        "static": "🔍 Static Analysis Findings",
        "review": "🧠 AI Code Review & Recommendations",
        "summary": "📊 Final Summary & Health Score"
    }

    for s in suggestions or []:
        stype = str(s.get("type", "")).lower()
        header = section_titles.get(stype, (s.get("type") or "Section").title())

        # Section title
        pdf.set_font("Auto" if unicode_mode else "Helvetica", "B", 14)
        pdf.set_text_color(30, 144, 255)
        pdf.cell(0, 9, sanitize(header), ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(3)

        # File & Issue info
        sub = f"File: {s.get('file', 'N/A')}  |  Line: {s.get('line', 0)}"
        pdf.set_font("Auto" if unicode_mode else "Helvetica", "", 11)
        pdf.multi_cell(0, 6, sanitize(sub))
        pdf.ln(1)

        issue = flatten_text(s.get("message", "No issue message"))
        pdf.multi_cell(0, 6, sanitize(f"Issue: {issue}"))
        pdf.ln(3)

        # Extract and format body
        body_text = flatten_text(s.get("suggestion", "No detailed output."))
        codes = extract_code_blocks(body_text)
        clean_body = re.sub(r"```(?:python)?(.*?)```", "", body_text, flags=re.DOTALL).strip()

        # Write recommendations
        if clean_body:
            pdf.set_font("Auto" if unicode_mode else "Helvetica", "", 10)
            pdf.multi_cell(0, 5.5, sanitize(clean_body))
            pdf.ln(3)

        # Write code suggestions separately
        if codes:
            for idx, code in enumerate(codes, start=1):
                pdf.set_font("Auto" if unicode_mode else "Helvetica", "B", 11)
                pdf.set_text_color(34, 139, 34)
                pdf.cell(0, 6, f"💡 Code Suggestion {idx}:", ln=True)
                pdf.set_font("Courier", "", 9)
                pdf.set_text_color(0, 0, 0)
                pdf.multi_cell(0, 4.5, sanitize(code))
                pdf.ln(4)
        else:
            pdf.set_font("Auto" if unicode_mode else "Helvetica", "I", 10)
            pdf.multi_cell(0, 5.5, sanitize("No code suggestions available."))
            pdf.ln(3)

        # Divider line
        y = pdf.get_y()
        pdf.line(10, y, 200, y)
        pdf.ln(6)

    # --- Full CrewAI Log / Final Output ---
    if full_output:
        pdf.add_page()
        pdf.set_font("Auto" if unicode_mode else "Helvetica", "B", 14)
        title2 = "🖥️ Full CrewAI Execution Log"
        pdf.set_text_color(220, 53, 69)
        pdf.cell(0, 9, sanitize(title2), ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Auto" if unicode_mode else "Helvetica", "", 9)

        # ✅ Flatten full_output safely
        text = flatten_text(full_output)
        text = clamp(text, 20000)
        text = re.sub(r"\x1b\[[0-9;]*m", "", text)
        pdf.multi_cell(0, 4.5, sanitize(text))


def generate_pdf_report(repo_url: str, suggestions: list, full_output=None) -> str:
    """Generate a clean, well-structured PDF report with Unicode or fallback fonts."""
    reports_dir = os.path.join("static", "reports")
    os.makedirs(reports_dir, exist_ok=True)
    out_path = os.path.join(reports_dir, f"devmate_report_{int(time.time())}.pdf")

    # Normalize full_output once
    def normalize_output(data):
        if isinstance(data, list):
            return "\n".join(
                f"- {x.get('type', 'Info')}: {x.get('suggestion', str(x))}"
                if isinstance(x, dict) else str(x)
                for x in data
            )
        elif isinstance(data, dict):
            return "\n".join(f"{k}: {v}" for k, v in data.items())
        return str(data or "")

    normalized_output = normalize_output(full_output)
    font_path = find_font()
    pdf = FPDF()

    try:
        if font_path:
            pdf.add_font("Auto", "", font_path, uni=True)
            pdf.add_font("Auto", "B", font_path, uni=True)
            _render_pdf(pdf, repo_url, suggestions, normalized_output, unicode_mode=True)
        else:
            raise RuntimeError("No Unicode font found; forcing fallback.")

        pdf.output(out_path)
        print(f"📄 Clean detailed PDF generated (Unicode): {out_path}")
        return f"reports/{os.path.basename(out_path)}"

    except Exception as e:
        print(f"⚠️ Unicode PDF failed ({e}); retrying with Helvetica fallback...")
        pdf = FPDF()
        try:
            normalized_output = normalize_output(full_output)
            _render_pdf(pdf, repo_url, suggestions, normalized_output, unicode_mode=False)
            pdf.output(out_path)
            print(f"📄 Clean detailed PDF generated (fallback): {out_path}")
        except Exception as fallback_error:
            print(f"❌ PDF generation failed in fallback mode: {fallback_error}")
            raise fallback_error

    return f"reports/{os.path.basename(out_path)}"
