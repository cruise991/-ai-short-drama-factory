from shared_tools.log_sanitizer import sanitize

def test_bearer_token_redacted():
    assert "***REDACTED***" in sanitize("Bearer sk-x4xG2tBIQm9gy1om2wkiFlmpzMBCyP7g")

def test_sk_prefix_redacted():
    assert "sk-***REDACTED***" in sanitize("Key: sk-OpWjgPwGXQT0g5xNj7ePDg")

def test_safe_text_unchanged():
    assert sanitize("Normal log message") == "Normal log message"
