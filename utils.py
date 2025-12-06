import os, shutil, tempfile, time

def make_workdir():
    d = os.path.join(tempfile.gettempdir(), f"devmate_{int(time.time())}")
    os.makedirs(d, exist_ok=True)
    return d

def list_py_files(root):
    for dirpath, _, files in os.walk(root):
        for f in files:
            if f.endswith(".py"):
                yield os.path.join(dirpath, f)

def clean_dir(path):
    try: shutil.rmtree(path, ignore_errors=True)
    except: pass
