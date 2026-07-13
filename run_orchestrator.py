import subprocess
import sys

p = subprocess.Popen(
    ["/Library/Developer/CommandLineTools/usr/bin/python3", "-u", "orchestrator.py"],
    stdin=subprocess.PIPE,
    stdout=sys.stdout,
    stderr=sys.stderr,
    text=True
)

p.communicate("在电梯内场景跳舞的视频，D1_dance_idol角色，9:16竖屏\n\n\n\n3\n")
