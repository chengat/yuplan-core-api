"""Section type mappings for course timetable scrapers.

This module provides a unified mapping of section type abbreviations
and variants to their canonical normalized forms.
"""

import re

# Section type mappings
# Format: (pattern, normalized_type)
SECTION_TYPE_MAPPINGS = [
    # Lecture
    ("LECT", "LECT"),
    ("LEC", "LECT"),
    # Laboratory
    ("LAB", "LAB"),
    # Tutorial
    ("TUTR", "TUTR"),
    ("TUT", "TUTR"),
    # Seminar
    ("SEMR", "SEMR"),
    ("SEMINAR", "SEMR"),
    ("SEM", "SEMR"),
    # Blended learning
    ("BLEN", "BLEN"),
    ("BLENDED", "BLEN"),
    # Online
    ("ONLN", "ONLN"),
    ("ONLINE", "ONLN"),
    ("ONL", "ONLN"),
    ("ONCA", "ONCA"),  # Online - Campus Assessment
    # Co-op
    ("COOP", "COOP"),
    ("COOPTERM", "COOP"),
    ("COOPWORKTERM", "COOP"),
    # Independent study
    ("ISTY", "ISTY"),
    ("INDEPENDENTSTUDY", "ISTY"),
    ("INDSTUDY", "ISTY"),
    ("DIRD", "DIRD"),  # Directed reading/study
    ("DIRECTEDSTUDY", "DIRD"),
    # Field experience
    ("FDEX", "FDEX"),
    ("FIELDEXERCISE", "FDEX"),
    ("FIEL", "FIEL"),  # Fieldwork
    ("FIELDWORK", "FIEL"),
    # Internship
    ("INSP", "INSP"),
    ("INTERNSHIP", "INSP"),
    # Research
    ("RESP", "RESP"),
    ("RESEARCH", "RESP"),
    ("REEV", "REEV"),  # Research evaluation
    ("RESEARCH EVALUATION", "REEV"),
    # Thesis
    ("THES", "THES"),
    ("THESIS", "THES"),
    # Workshop
    ("WRKS", "WRKS"),
    ("WRK", "WRKS"),
    ("WORKSHOP", "WRKS"),
    ("WKSP", "WKSP"),  # Alternative workshop abbreviation
    # Other
    ("PRAC", "PRAC"),  # Practicum
    ("PRA", "PRAC"),
    ("STUDIO", "STUDIO"),
    ("CLIN", "CLIN"),  # Clinical
    ("CLINICAL", "CLIN"),
    ("HYFX", "HYFX"),  # Hybrid flex
    ("HYBRIDFLEX", "HYFX"),
]


def get_section_type(text: str, norm_text_func) -> str:
    normalized_text = norm_text_func(text).upper()
    compact_text = re.sub(r"[^A-Z]", "", normalized_text)
    
    for pattern, normalized_type in SECTION_TYPE_MAPPINGS:
        if pattern in compact_text:
            return normalized_type
    
    return ""

