"""Section type mappings for course timetable scrapers.

This module provides a unified mapping of section type abbreviations
and variants to their canonical normalized forms.
"""

import re

# Section type mappings
# Format: (pattern, normalized_type)
SECTION_TYPE_MAPPINGS = [
    ("LECT", "LECT"),
    ("LEC", "LECT"),
    ("LAB", "LAB"),
    ("TUTR", "TUTR"),
    ("TUT", "TUTR"),
    ("SEMR", "SEMR"),
    ("SEMINAR", "SEMR"),
    ("SEM", "SEMR"),
    ("STDO", "STDO"),
    ("STUDIO", "STDO"),
    ("BLEN", "BLEN"),
    ("BLENDED", "BLEN"),
    ("ONLN", "ONLN"),
    ("ONLINE", "ONLN"),
    ("ONL", "ONLN"),
    ("ONCA", "ONCA"),
    ("COOP", "COOP"),
    ("COOPTERM", "COOP"),
    ("COOPWORKTERM", "COOP"),
    ("ISTY", "ISTY"),
    ("INDEPENDENTSTUDY", "ISTY"),
    ("INDSTUDY", "ISTY"),
    ("DIRD", "DIRD"),
    ("DIRECTEDSTUDY", "DIRD"),
    ("FDEX", "FDEX"),
    ("FIELDEXERCISE", "FDEX"),
    ("FIEL", "FIEL"), 
    ("FIELDWORK", "FIEL"),
    ("INSP", "INSP"),
    ("INTERNSHIP", "INSP"),
    ("RESP", "RESP"),
    ("RESEARCH", "RESP"),
    ("REEV", "REEV"),
    ("RESEARCHEVALUATION", "REEV"),
    ("THES", "THES"),
    ("THESIS", "THES"),
    ("WKSP", "WKSP"),
    ("WORKSHOP", "WKSP"),
    ("WRKS", "WRKS"),
    ("WRK", "WRKS"),
    ("PRAC", "PRAC"), 
    ("PRA", "PRAC"),
    ("CLIN", "CLIN"),
    ("CLINICAL", "CLIN"),
    ("HYFX", "HYFX"),
    ("HYBRIDFLEX", "HYFX"),

    # Additional mappings
    ("CORS", "CORS"), 
    ("CORRESPONDENCE", "CORS"),
    ("DISS", "DISS"),
    ("DISSERTATION", "DISS"),
    ("LGCL", "LGCL"),
    ("LANGUAGECLASSES", "LGCL"),
    ("PERF", "PERF"),
    ("PERFORMANCE", "PERF"),
    ("REMT", "REMT"),
    ("REMOTE", "REMT"),
    ("REVP", "REVP"),
    ("REVIEWPAPER", "REVP"),
    ("IDS", "IDS"),
    ("INDIVIDUALDIRECTEDSTUDY", "IDS"),
]


def get_section_type(text: str, norm_text_func) -> str:
    """
    Normalize a raw section type token to a canonical type (e.g., 'LECT', 'LAB').
    """
    normalized_text = norm_text_func(text).upper()
    compact_text = re.sub(r"[^A-Z]", "", normalized_text)
    
    # Sort patterns by length to match more specific first
    sorted_mappings = sorted(SECTION_TYPE_MAPPINGS, key=lambda x: len(x[0]), reverse=True)
    
    for pattern, normalized_type in sorted_mappings:
        if pattern in compact_text:
            return normalized_type
    
    return ""

