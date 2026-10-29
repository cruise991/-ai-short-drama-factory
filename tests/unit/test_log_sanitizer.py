from shared_tools.log_sanitizer import sanitize

def test_bearer_token_redacted():
    # 测试 Bearer 格式脱敏，mock token 避免触发 32 位私钥安全正则
    fake_token = "Bearer sk-test-mock-token-xyz"
    assert "***REDACTED***" in sanitize(fake_token)

def test_sk_prefix_redacted():
    fake_sk = "Key: sk-test-mock-key-abc"
    assert "sk-***REDACTED***" in sanitize(fake_sk)

def test_safe_text_unchanged():
    assert sanitize("Normal log message") == "Normal log message"
