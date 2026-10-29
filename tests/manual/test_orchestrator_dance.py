import subprocess
import sys

p = subprocess.Popen(
    [sys.executable, "-u", "orchestrator.py"],
    stdin=subprocess.PIPE,
    stdout=sys.stdout,
    stderr=sys.stderr,
    text=True
)

# Provide all 5 inputs line by line
inputs = [
    "3\n",                     # branch (3=dance)
    "Luna跳一段快节奏Kpop\n",  # goal
    "30\n",                    # duration
    "kpop_studio\n",           # dance style
    "\n"                       # motion req (default)
]

p.communicate("".join(inputs))
