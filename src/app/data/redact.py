
import re
def scrub(text: str) -> str:
    t = text or ""
    t = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[SSN]", t)
    t = re.sub(r"\b\d{3}[- ]\d{3}[- ]\d{4}\b", "[PHONE]", t)
    t = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[EMAIL]", t)
    t = re.sub(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b", "[DATE]", t)
    return t.strip()
