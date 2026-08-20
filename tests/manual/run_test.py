import subprocess
import time
import os

if __name__ == "__main__":
    workspace_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    proc = subprocess.Popen(
        ["python3", "orchestrator.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        cwd=workspace_dir
    )

    inputs = ["2", "n", "4", "3", "1", "30"]

    for i in inputs:
        print(f"Sending: {i}")
        proc.stdin.write(i + "\n")
        proc.stdin.flush()
        time.sleep(1)

    proc.stdin.close()
    stdout, stderr = proc.communicate()
    print("STDOUT:")
    print(stdout)
    print("STDERR:")
    print(stderr)
