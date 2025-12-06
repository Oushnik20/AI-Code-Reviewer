import os, json, subprocess, sys
from git import Repo
from utils import make_workdir, list_py_files

def run_cmd(cmd, cwd=None):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr

def clone_repo(git_url:str)->str:
    workdir = make_workdir()
    print(f"📂 Cloning repo: {git_url}")
    Repo.clone_from(git_url, workdir, depth=1)
    return workdir

def run_pylint(root):
    results = []
    for i, f in enumerate(list_py_files(root)):
        # if i >= 2:  # limit for speed
        #     break
        print("🔍 Running pylint on", f)
        cmd = [sys.executable, "-m", "pylint", f, "--output-format=json"]
        code, out, err = run_cmd(cmd)
        try:
            issues = json.loads(out or "[]")
        except Exception as e:
            print("⚠️ Error parsing pylint output:", e)
            issues = []
        results.append({"file": f, "issues": issues})
    return results

def run_bandit(root):
    print("🛡️ Running bandit...")
    cmd = [sys.executable, "-m", "bandit", "-r", root, "-f", "json"]
    code, out, err = run_cmd(cmd)
    try:
        return json.loads(out or "{}")
    except:
        return {"results": []}

def run_radon_complexity(root):
    print("📈 Running radon complexity...")
    cmd = [sys.executable, "-m", "radon", "cc", "-j", root]
    code, out, err = run_cmd(cmd)
    try:
        return json.loads(out or "{}")
    except:
        return {}

def analyze_repository(git_url:str)->dict:
    repo_dir = clone_repo(git_url)
    pylint_findings = run_pylint(repo_dir)
    bandit_findings = run_bandit(repo_dir)
    radon_findings = run_radon_complexity(repo_dir)
    return {
        "repo_dir": repo_dir,
        "pylint": pylint_findings,
        "bandit": bandit_findings,
        "radon": radon_findings,
    }
