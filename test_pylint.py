from analyzer import run_pylint, clone_repo
print("Cloning...")
repo = clone_repo("https://github.com/psf/requests.git")
print("Running pylint on few files...")
results = run_pylint(repo)
print("✅ Done. Files analyzed:", len(results))
for r in results[:2]:
    print(r["file"], "=>", len(r["issues"]), "issues")
