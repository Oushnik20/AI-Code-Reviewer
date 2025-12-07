# patch_crewai.py — ensures CrewAI never triggers LiteLLM fallback
import importlib

try:
    spec = importlib.util.find_spec("crewai.utilities.llm_utils")
    if spec:
        llm_utils = importlib.import_module("crewai.utilities.llm_utils")
        def safe_create_llm(obj): return obj
        llm_utils.create_llm = safe_create_llm
        print("✅ CrewAI global patch applied")
except Exception as e:
    print("⚠️ Patch failed:", e)
