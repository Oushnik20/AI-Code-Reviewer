# early_patch.py — absolutely prevent LiteLLM fallback

import builtins, importlib

def patch_crewai_llm():
    try:
        spec = importlib.util.find_spec("crewai.utilities.llm_utils")
        if spec:
            m = importlib.import_module("crewai.utilities.llm_utils")
            def no_fallback(obj): 
                print("✅ CrewAI create_llm override active")
                return obj
            m.create_llm = no_fallback
            print("✅ CrewAI hard patch applied")
    except Exception as e:
        print("⚠️ CrewAI patch failed:", e)

builtins.__dict__["patch_crewai_llm"] = patch_crewai_llm
patch_crewai_llm()
