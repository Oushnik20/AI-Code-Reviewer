🚀 DevMate – AI-Powered Code Analyzer

DevMate is an intelligent multi-agent code analysis platform that reviews GitHub repositories using AI.
It performs static analysis, reasoning-based code reviews, and generates detailed PDF reports — all powered by CrewAI, LangChain, and Groq LLMs.

Live:
```bash
https://oushnik20-raya-space.hf.space/
```

⚡ Features

🧠 AI Multi-Agent Review – Combines static and reasoning agents for in-depth analysis

🧮 Static Tools Integration – Uses Pylint, Bandit, and Radon for code metrics

📄 Automated PDF Reports – Detailed code insights with improvement suggestions

🌐 Web Dashboard – Upload repo URLs and view all analyses

🔒 Secure Secrets – Groq API keys managed via .env or Render environment variables

🧰 Tech Stack

Backend: Flask + SQLAlchemy

AI Engine: CrewAI + LangChain + Groq

Static Analysis: Pylint, Bandit, Radon

PDF Reports: FPDF

Deployment: Render (Gunicorn)

⚙️ Installation (Local)
```bash
git clone https://github.com/Oushnik20/devmate.git

cd devmate

pip install -r requirements.txt
```

Create a .env file:

GROQ_API_KEY=your_groq_api_key_here


Run locally:

python app.py


Open in browser → http://127.0.0.1:5000

☁️ Deployment (Render)

Push your project to GitHub

Go to Render.com
 → “New Web Service”

Set:

Build Command: pip install -r requirements.txt

Start Command: gunicorn app:app

Add Environment Variable:
GROQ_API_KEY = your_api_key

Deploy 🎯

🧾 Example Output

After analysis, DevMate generates:

Code health report

AI review suggestions

Downloadable PDF with details

🧑‍💻 Author

Oushnik Banerjee
Smart code analysis, simplified.
