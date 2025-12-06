# Force LiteLLM to preload (Render isolation fix)
import importlib.util, sys

if importlib.util.find_spec("litellm") is None:
    print("⚠️ LiteLLM module not found — reinstalling dynamically")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "litellm"], check=False)
else:
    print("✅ LiteLLM preloaded successfully")

from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import os
from flask_sqlalchemy import SQLAlchemy
from agents import analyze_repo_with_agents
from reporter import generate_pdf_report

app = Flask(__name__)
app.secret_key = "devmate_secret"

# ---------- Database Setup ----------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'devmate.db')}"
db = SQLAlchemy(app)


# ---------- Model ----------
class Analysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    repo_name = db.Column(db.String(300), nullable=False)
    score = db.Column(db.Float, nullable=False)
    pdf_path = db.Column(db.String(300), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


with app.app_context():
    db.create_all()


# ---------- Routes ----------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        repo_url = request.form.get("repo_url", "").strip()

        if not repo_url:
            flash("⚠️ Please enter a GitHub repository URL.", "warning")
            return redirect(url_for("index"))

        try:
            print(f"🤖 Starting multi-agent review for: {repo_url}")

            # Step 1: Run AI multi-agent analysis
            result_text = analyze_repo_with_agents(repo_url)
            print("✅ Step 1: Analysis complete")

            # Wrap result for PDF
            suggestions = [{
                "type": "summary",
                "file": "",
                "line": 0,
                "message": "Detailed Multi-Agent AI Report",
                "suggestion": result_text
            }]

            # Step 2: Extract score
            score = extract_score(result_text)
            print(f"✅ Step 2: Score = {score}")

            # Step 3: Pre-save placeholder entry (prevents missing report)
            record = Analysis(repo_name=repo_url, score=score, pdf_path="Generating...")
            db.session.add(record)
            db.session.commit()
            print("✅ Step 3: Placeholder record saved")

            # Step 4: Generate PDF report
            try:
                pdf_path = generate_pdf_report(repo_url, suggestions, result_text)
                # Ensure path is relative for dashboard links
                if pdf_path.startswith("static/"):
                    pdf_path = pdf_path.replace("static/", "")
                record.pdf_path = pdf_path
                db.session.commit()
                print(f"✅ Step 4: PDF generated and record updated at {pdf_path}")
            except Exception as pdf_err:
                record.pdf_path = "Error generating PDF"
                db.session.commit()
                print(f"⚠️ PDF generation failed: {pdf_err}")

            flash("✅ Full detailed analysis complete! View report in Dashboard.", "success")
            return redirect(url_for("dashboard"))

        except Exception as e:
            print("❌ Error during analysis:")
            import traceback
            traceback.print_exc()
            flash(f"❌ Analysis failed: {e}", "danger")
            return redirect(url_for("index"))

    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    analyses = Analysis.query.order_by(Analysis.timestamp.desc()).all()
    return render_template("dashboard.html", analyses=analyses)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


# ---------- Utility ----------
def extract_score(text):
    """Extract numeric score from any format (string, list, or dict)."""
    if isinstance(text, list):
        text = " ".join(
            t.get("suggestion", "") if isinstance(t, dict) else str(t)
            for t in text
        )
    elif isinstance(text, dict):
        text = text.get("suggestion", "") or text.get("result", "") or str(text)
    else:
        text = str(text)

    for token in text.split():
        if "/10" in token or token.replace(".", "", 1).isdigit():
            try:
                val = float(token.strip("/10"))
                if 0 < val <= 10:
                    return round(val, 2)
            except ValueError:
                continue
    return 7.5

port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port, debug=True)
if __name__ == "__main__":
    app.run(debug=True)
