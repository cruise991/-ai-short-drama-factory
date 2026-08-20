import pexpect
import sys

child = pexpect.spawn("python3 orchestrator.py", encoding="utf-8")
child.logfile = sys.stdout
child.expect(".*4.*")
child.sendline("4")
child.expect(".*按回车键开始精确恢复.*")
child.sendline("")
child.expect(pexpect.EOF, timeout=3000)
