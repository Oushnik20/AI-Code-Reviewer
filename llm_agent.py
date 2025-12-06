import os, time
from dotenv import load_dotenv

load_dotenv()
from groq import Groq

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
USE_LLM = bool(GROQ_API_KEY)
client = Groq(api_key=GROQ_API_KEY) if USE_LLM else None
MODEL = "llama3-70b-8192"

# -------- offline fallback --------
def offline_hint(issue):
    msg = (issue.get("message") or "").lower()
    if "line too long" in msg:
        return "Keep lines ≤ 100 chars. Break long expressions or strings."
    if "missing module docstring" in msg:
        return "Add a top-level docstring describing purpose & usage."
    if "missing class docstring" in msg:
        return "Add a short docstring summarizing the class."
    if "wildcard import" in msg:
        return "Avoid 'from X import *'; import only needed names."
    if "unable to import" in msg:
        return "Install or correctly reference the missing module."
    return "Review and refactor for clarity; follow PEP-8 and security best practices."

# -------- chat helper --------
def _chat(prompt: str, retries=3):
    if not USE_LLM:
        raise RuntimeError("LLM_DISABLED")
    delay = 2
    for _ in range(retries):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are DevMate, a senior Python code reviewer. Reply with short 'Why' + 'Fix'.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            msg = str(e).lower()
            if "rate" in msg or "quota" in msg:
                time.sleep(delay)
                delay = min(delay * 2, 16)
                continue
            raise
    raise RuntimeError("LLM_RATE_LIMIT")

def build_prompt(file_path, msg, line, symbol):
    return (
        f"File: {file_path}\nLine: {line}\nIssue: {msg}\nSymbol: {symbol}\n\n"
        "Explain briefly why it’s a problem and give a minimal safe fix."
    )

# -------- main reasoning --------
def reason_over_findings(analysis: dict, max_llm_calls: int = 8) -> list:
    suggestions = []
    llm_budget = max_llm_calls

    # --- pylint ---
    for entry in analysis.get("pylint", []):
        f = entry["file"]
        for iss in entry.get("issues", [])[:max_llm_calls]:
            msg, line, sym = iss.get("message",""), iss.get("line",""), iss.get("symbol","")
            prompt = build_prompt(f, msg, line, sym)
            try:
                suggestion = _chat(prompt) if llm_budget > 0 else offline_hint(iss)
                llm_budget -= 1
            except Exception:
                suggestion = offline_hint(iss)
            suggestions.append({"type":"pylint","file":f,"line":line,"message":msg,"suggestion":suggestion})

    # --- bandit ---
    for iss in analysis.get("bandit", {}).get("results", [])[:3]:
        f = iss.get("filename",""); ln = iss.get("line_number",""); msg = iss.get("issue_text","")
        prompt = f"Security issue in {f}:{ln}\n{msg}\nExplain risk + safe fix."
        try:
            suggestion = _chat(prompt) if llm_budget>0 else offline_hint(iss)
            llm_budget -= 1
        except Exception:
            suggestion = offline_hint(iss)
        suggestions.append({"type":"bandit","file":f,"line":ln,"message":msg,"suggestion":suggestion})

    # --- radon ---
    for f, items in list(analysis.get("radon", {}).items())[:3]:
        for it in items[:2]:
            n, r, ln = it.get("name",""), it.get("rank",""), it.get("lineno","")
            prompt = f"{f}:{ln} has complexity rank {r}. Suggest a refactor outline."
            try:
                suggestion = _chat(prompt) if llm_budget>0 else offline_hint(it)
                llm_budget -= 1
            except Exception:
                suggestion = offline_hint(it)
            suggestions.append({"type":"radon","file":f,"line":ln,"message":f"Complexity {r}","suggestion":suggestion})

    return suggestions
