import re
from typing import Optional, Tuple

# Each detector returns either:
#   (type, token_or_url)
# or None if the URL doesn't match

def detect_greenhouse(url: str) -> Optional[Tuple[str, str]]:
    # Prefer API token (stable & structured)
    m = re.search(r"boards-api\.greenhouse\.io/v1/boards/([^/]+)/jobs", url)
    if m:
        return ("greenhouse_api", m.group(1))
    # Fallback: embed token
    m = re.search(r"boards\.greenhouse\.io/embed/job_board\?for=([a-zA-Z0-9\-_]+)", url)
    if m:
        return ("greenhouse_embed", url)
    return None

def detect_lever(url: str) -> Optional[Tuple[str, str]]:
    m = re.search(r"jobs\.lever\.co/([a-zA-Z0-9\-_]+)", url)
    if m:
        return ("lever", m.group(1))
    return None

def detect_workday(url: str) -> Optional[Tuple[str, str]]:
    # Workday tenants are subdomains on myworkdayjobs.com
    m = re.search(r"([a-zA-Z0-9\-_]+)\.myworkdayjobs\.com", url)
    if m:
        return ("workday", m.group(1))
    return None

def detect_ashby(url: str) -> Optional[Tuple[str, str]]:
    m = re.search(r"jobs\.ashbyhq\.com/([a-zA-Z0-9\-_]+)", url)
    if m:
        return ("ashby", m.group(1))
    return None

def detect_smartrecruiters(url: str) -> Optional[Tuple[str, str]]:
    m = re.search(r"careers\.smartrecruiters\.com/([a-zA-Z0-9\-_]+)", url)
    if m:
        return ("smartrecruiters", m.group(1))
    return None

def detect_successfactors(url: str) -> Optional[Tuple[str, str]]:
    # SuccessFactors URLs vary widely; treat any presence as a match for now
    if "successfactors.com" in url:
        return ("successfactors", url)
    return None

def detect_ats(url: str):
    """Try all detectors; return first match or None."""
    for fn in (
        detect_greenhouse,
        detect_lever,
        detect_workday,
        detect_ashby,
        detect_smartrecruiters,
        detect_successfactors,
    ):
        r = fn(url)
        if r:
            return r
    return None
