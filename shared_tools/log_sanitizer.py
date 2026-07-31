import re

_SENSITIVE_PATTERNS = [
    (re.compile(r'(Bearer\s+)\S+', re.I), r'\1***REDACTED***'),
    (re.compile(r'(sk-)\S+'), r'\1***REDACTED***'),
    (re.compile(r'(wk-)\S+'), r'\1***REDACTED***'),
    (re.compile(r'(X-goog-api-key:\s*)\S+', re.I), r'\1***REDACTED***'),
    (re.compile(r'(Authorization:\s*)\S+', re.I), r'\1***REDACTED***'),
]

def sanitize(text: str) -> str:
    for pattern, replacement in _SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text
