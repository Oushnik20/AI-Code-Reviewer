from analyzer import clone_repo
print("Cloning…")
path = clone_repo("https://github.com/psf/requests.git")
print("✅ Cloned to:", path)
