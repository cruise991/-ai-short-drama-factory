import os
import gzip
import hashlib
import tempfile
import subprocess
import pytest
from server.core.logging import sanitize_log_content, JSONFormatter
import logging
import json

def test_backup_and_checksum_verification():
    """Test SHA-256 checksum generation and integrity detection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        backup_file = os.path.join(tmpdir, "pg_backup_test.sql.gz")
        dummy_sql = b"CREATE TABLE users (id SERIAL PRIMARY KEY, username VARCHAR(50));\n"
        with gzip.open(backup_file, "wb") as f:
            f.write(dummy_sql)

        # Compute SHA-256
        sha256_hash = hashlib.sha256()
        with open(backup_file, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        expected_hex = sha256_hash.hexdigest()

        checksum_file = f"{backup_file}.sha256"
        with open(checksum_file, "w") as f:
            f.write(f"{expected_hex}  {os.path.basename(backup_file)}\n")

        # Verify matching checksum
        with open(backup_file, "rb") as f:
            verified_hash = hashlib.sha256(f.read()).hexdigest()
        assert verified_hash == expected_hex

        # Simulate tampering
        with open(backup_file, "ab") as f:
            f.write(b"TAMPERED_CONTENT")
        with open(backup_file, "rb") as f:
            tampered_hash = hashlib.sha256(f.read()).hexdigest()
        assert tampered_hash != expected_hex


def test_restore_script_validation():
    """Test restore_postgres.sh script argument validation and non-existent file handling."""
    script_path = os.path.abspath("scripts/restore_postgres.sh")
    assert os.path.exists(script_path), "restore_postgres.sh must exist"

    # Test missing argument
    res_no_args = subprocess.run(["bash", script_path], capture_output=True, text=True)
    assert res_no_args.returncode == 1
    assert "Usage:" in res_no_args.stdout or "Usage:" in res_no_args.stderr

    # Test non-existent file
    res_missing = subprocess.run(["bash", script_path, "/tmp/non_existent_dump_xyz.sql.gz"], capture_output=True, text=True)
    assert res_missing.returncode != 0
    assert "does not exist" in res_missing.stdout or "does not exist" in res_missing.stderr


def test_log_sanitizer_secrets_redaction():
    """Verify log sanitization for API keys, tokens, DB connections and passwords."""
    raw_text = (
        "Connected to postgresql://admin:SuperSecretPass123!@postgres.internal:5432/shortdrama_db. "
        "User token: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xyz. "
        "Called Agnes model with key sk-99887766554433221100. "
        "Redis URI: redis://:my_strong_redis_pwd@127.0.0.1:6379/0. "
        "Config dump: password='prod_password_to_mask'."
    )
    sanitized = sanitize_log_content(raw_text)

    # Assert secrets are redacted
    assert "SuperSecretPass123!" not in sanitized
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xyz" not in sanitized
    assert "sk-99887766554433221100" not in sanitized
    assert "my_strong_redis_pwd" not in sanitized
    assert "prod_password_to_mask" not in sanitized

    # Assert REDACTED markers are present
    assert "***REDACTED***" in sanitized


def test_json_formatter_structured_sanitization():
    """Verify JSONFormatter automatically masks secrets in record message and exceptions."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test.logger",
        level=logging.ERROR,
        pathname="test.py",
        lineno=42,
        msg="Error calling service: Bearer secret_access_token_12345678",
        args=(),
        exc_info=None
    )
    formatted = formatter.format(record)
    data = json.loads(formatted)

    assert "secret_access_token_12345678" not in data["message"]
    assert "Bearer ***REDACTED***" in data["message"]
    assert data["level"] == "ERROR"
    assert data["line"] == 42
