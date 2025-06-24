from gitingest.security.secret_scan import redact_secrets


def test_redact_basic():
    secret_text = 'AWS_SECRET_ACCESS_KEY = "ABCD1234EFGH5678IJKL"'
    cleaned = redact_secrets(secret_text)
    assert 'ABCD' not in cleaned
    assert '\u2605' in cleaned
