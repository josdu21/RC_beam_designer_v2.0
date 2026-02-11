import os
import sys
import subprocess

def run():
    # Construct the command to run streamlit via python module
    cmd = [sys.executable, "-m", "streamlit", "run", "app.py"]
    print(f"Running command: {' '.join(cmd)}")
    subprocess.run(cmd)

if __name__ == "__main__":
    run()
