import os, sys, subprocess, importlib.util, re
from dotenv import load_dotenv

# --- Load environment ---
load_dotenv()
if not os.getenv("GROQ_API_KEY"):
    raise EnvironmentError("❌ Missing GROQ_API_KEY — please set it in Render.")

# --- Ensure LiteLLM is installed ---
if importlib.util.find_spec("litellm") is None:
    print("⚙️ Installing LiteLLM...")
    subprocess.run([sys.executable, "-m", "pip", "install", "litellm==1.35.5"], check=False)

# --- Use Groq directly ---
from langchain_groq import ChatGroq
llm = ChatGroq(
    model="groq/llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.3
)
print("✅ Groq LLM initialized successfully")

# --- Patch CrewAI to accept external LLMs ---
import crewai.utilities.llm_utils as llm_utils
def safe_create_llm(obj):
    return obj  # just return the provided llm instance
llm_utils.create_llm = safe_create_llm

from crewai import Agent, Task, Crew
from analyzer import analyze_repository

# -----------------------------
# Helper to clean output text
# -----------------------------
def clean_text(data):
    """Recursively remove emojis, non-ASCII chars, and normalize to plain text."""
    if isinstance(data, list):
        return [clean_text(x) for x in data]
    elif isinstance(data, dict):
        return {k: clean_text(v) for k, v in data.items()}
    elif data is None:
        return ""
    
    # Convert to string
    text = str(data)

    # Remove emoji and non-ASCII safely
    text = re.sub(r"[^\x00-\x7F]+", "", text)

    # Extra cleanup — strip CrewAI markers or markdown leftovers
    text = re.sub(r"`+", "", text)
    text = text.replace("•", "-").replace("–", "-").replace("—", "-")

    return text.strip()


# -----------------------------
# AGENTS (with no-emoji constraint)
# -----------------------------
StaticAgent = Agent(
    role="Static Analysis Expert",
    goal=(
        "Analyze the repository and extract Pylint, Bandit, and Radon results. "
        "Write your output using plain text only — do not include emojis, icons, "
        "or special Unicode characters. Use clear English and markdown formatting if needed."
    ),
    backstory=(
        "You are a senior code reviewer who runs static tools and summarizes issues "
        "in a professional, technical manner without any decorative symbols."
    ),
    llm=llm
)

ReasoningAgent = Agent(
    role="Code Reviewer AI",
    goal=(
        "Read static analysis results and provide concise, actionable fixes. "
        "Use only plain text. Avoid emojis, decorative symbols, or Unicode icons. "
        "Keep formatting simple and professional — headings and bullet points only."
    ),
    backstory=(
        "You specialize in providing clear, structured, and professional code improvement "
        "recommendations suitable for developer reports."
    ),
    llm=llm
)

SummarizerAgent = Agent(
    role="Report Generator",
    goal=(
        "Summarize findings, calculate the overall code quality score, and structure "
        "the report using plain technical English. Avoid emojis or special characters. "
        "Keep the tone professional and focused on actionable insights."
    ),
    backstory=(
        "You are responsible for generating developer-friendly summaries and "
        "objective scores without any decorative elements."
    ),
    llm=llm
)


# -----------------------------
# MAIN WORKFLOW
# -----------------------------
def analyze_repo_with_agents(repo_url: str):
    print("⚙️ Running StaticAgent...")
    analysis = analyze_repository(repo_url)

    # --- Tasks ---
    static_task = Task(
        description=(
            f"Run static analysis on {repo_url} and explain the Pylint, Bandit, "
            f"and Radon results clearly using plain text (no emojis)."
        ),
        expected_output="Detailed explanation of static analysis results in plain text.",
        agent=StaticAgent
    )

    reasoning_task = Task(
        description=(
            f"Read the static analysis report for {repo_url} and provide improvements, "
            f"reasoning, and refactor suggestions in plain text (no emojis)."
        ),
        expected_output="Structured AI review with actionable feedback in clean text.",
        agent=ReasoningAgent,
        context=[static_task]
    )

    summary_task = Task(
        description=(
            f"Summarize repository health, list detected issues, and recommendations, "
            f"and assign a numeric score (1–10). Output must be plain text — no emojis."
        ),
        expected_output="Full summary with numeric quality score in ASCII text.",
        agent=SummarizerAgent,
        context=[reasoning_task]
    )

    # --- Crew Workflow ---
    crew = Crew(
        agents=[StaticAgent, ReasoningAgent, SummarizerAgent],
        tasks=[static_task, reasoning_task, summary_task],
        verbose=True
    )

    print("🚀 Running DevMate CrewAI Workflow...")
    result = crew.kickoff()

    # --- Clean all outputs ---
    static_output = clean_text(static_task.output)
    reasoning_output = clean_text(reasoning_task.output)
    summary_output = clean_text(summary_task.output)

    # --- Return structured results ---
    return [
        {"type": "static", "file": repo_url, "line": 0, "message": "Static Analysis", "suggestion": static_output},
        {"type": "review", "file": repo_url, "line": 0, "message": "Code Review", "suggestion": reasoning_output},
        {"type": "summary", "file": repo_url, "line": 0, "message": "Final Summary", "suggestion": summary_output},
    ]
