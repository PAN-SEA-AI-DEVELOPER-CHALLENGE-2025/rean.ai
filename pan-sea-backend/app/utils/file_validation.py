import os
import logging
from typing import Optional


logger = logging.getLogger(__name__)


ALLOWED_EXTENSIONS = {".pdf", ".pptx", ".docx", ".txt"}
ALLOWED_MAGIC = {
    ".pdf": b"%PDF",
    ".pptx": b"PK\x03\x04",  # zip-based
    ".docx": b"PK\x03\x04",  # zip-based
    ".txt": None,  # plain text flexible
}


def sniff_magic(file_path: str, ext: str, read_len: int = 8) -> bool:
    try:
        magic = ALLOWED_MAGIC.get(ext)
        if magic is None:
            # For txt, allow anything readable; no strict magic
            return True
        with open(file_path, "rb") as f:
            header = f.read(read_len)
            return header.startswith(magic)
    except Exception as e:
        logger.warning(f"Magic sniff failed for {file_path}: {e}")
        return False


def clamav_scan(file_path: str) -> Optional[str]:
    """Scan using clamd if available. Returns None if clean, else reason string.
    Non-fatal if clamd is not available; returns None in that case.
    """
    try:
        import clamd  # type: ignore
        try:
            cd = clamd.ClamdUnixSocket()
            result = cd.scan(file_path)
        except Exception:
            try:
                cd = clamd.ClamdNetworkSocket(host="127.0.0.1", port=3310)
                result = cd.scan(file_path)
            except Exception:
                return None
        # result format: {"/path": ("FOUND"|"OK", "Malware.Name"|None)}
        if isinstance(result, dict):
            status, reason = next(iter(result.values()))
            if status and str(status).upper() == "FOUND":
                return str(reason or "malware detected")
        return None
    except Exception:
        return None


def validate_material_file(file_path: str, original_name: Optional[str] = None, max_size: int = 25 * 1024 * 1024) -> Optional[str]:
    """Return None if valid, else error message string."""
    try:
        ext = os.path.splitext(original_name or file_path)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return f"Unsupported file extension: {ext}"
        # size check
        size = os.path.getsize(file_path)
        if size > max_size:
            return f"File too large: {size} bytes (max {max_size})"
        # magic sniff
        if not sniff_magic(file_path, ext):
            return "File content does not match the expected format"
        # AV scan (best-effort)
        malware_reason = clamav_scan(file_path)
        if malware_reason:
            return f"Malware detected: {malware_reason}"
        return None
    except Exception as e:
        logger.warning(f"Validation failed for {file_path}: {e}")
        return "Validation failed"


