import re

_SECTION_HEADERS: dict[str, list[str]] = {
    "experience": [
        r"professional\s+experience",
        r"work\s+experience",
        r"work\s+history",
        r"employment",
        r"experience",
    ],
    "skills": [
        r"technical\s+skills",
        r"core\s+competencies",
        r"competencies",
        r"technologies",
        r"tools",
        r"skills",
    ],
    "education": [
        r"education",
        r"academic\s+background",
        r"academic",
        r"qualifications",
        r"degrees",
    ],
    "summary": [
        r"professional\s+summary",
        r"executive\s+summary",
        r"summary",
        r"objective",
        r"profile",
        r"about\s+me",
        r"about",
    ],
}


def _detect_header(line: str) -> str | None:
    """Return section type if line looks like a section header, else None."""
    stripped = line.strip().rstrip(":").strip()
    if not stripped or len(stripped) > 60:
        return None
    # Try each section's patterns, longest/most-specific first
    for stype, patterns in _SECTION_HEADERS.items():
        for pat in patterns:
            if re.fullmatch(pat, stripped, re.IGNORECASE):
                return stype
    return None


def parse_sections(text: str) -> dict[str, str]:
    """
    Parse resume text into named sections by detecting header lines.

    Returns dict mapping section_type → content string.
    Falls back to {"other": text} when no recognisable headers found.
    """
    if not text or not text.strip():
        return {"other": text}

    lines = text.splitlines()
    sections: dict[str, list[str]] = {}
    current: str | None = None

    for line in lines:
        stype = _detect_header(line)
        if stype is not None:
            current = stype
            sections.setdefault(current, [])
        elif current is not None:
            sections[current].append(line)

    non_empty = {k: "\n".join(v).strip() for k, v in sections.items() if any(l.strip() for l in v)}
    return non_empty if non_empty else {"other": text}
