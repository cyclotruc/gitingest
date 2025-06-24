from detect_secrets.core import scan
from detect_secrets.settings import default_settings
from threading import Lock


_lock = Lock()


def redact_secrets(text: str) -> str:
    """Return text with detected secrets replaced by stars."""
    if not any(ch.isdigit() or ch.isupper() for ch in text):
        return text
    lines = text.splitlines(keepends=True)
    with _lock, default_settings():
        for i, line in enumerate(lines):
            redacted_line = line
            for secret in scan.scan_line(line):
                secret_value = secret.secret_value
                if not secret_value:
                    continue
                idx = redacted_line.find(secret_value)
                if idx == -1:
                    continue
                mask_len = max(4, int(len(secret_value) * 0.8))
                redacted_line = (
                    redacted_line[:idx] + "\u2605" * mask_len + redacted_line[idx + mask_len :]
                )
            lines[i] = redacted_line
    return "".join(lines)
