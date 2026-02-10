"""Tests for section type mappings and normalization."""

import unittest

from scraping.scrapers.helpers.text_utils import norm_text
from scraping.scrapers.helpers.section_types import get_section_type, SECTION_TYPE_MAPPINGS


class TestSectionTypes(unittest.TestCase):
    """Test section type normalization and mappings."""

    def test_lecture_variants(self):
        """Test lecture section type variants."""
        self.assertEqual(get_section_type("LEC", norm_text), "LECT")
        self.assertEqual(get_section_type("LECT", norm_text), "LECT")
        self.assertEqual(get_section_type("Lecture", norm_text), "LECT")
        self.assertEqual(get_section_type("lect", norm_text), "LECT")

    def test_laboratory(self):
        """Test laboratory section type."""
        self.assertEqual(get_section_type("LAB", norm_text), "LAB")
        self.assertEqual(get_section_type("Laboratory", norm_text), "LAB")

    def test_tutorial_variants(self):
        """Test tutorial section type variants."""
        self.assertEqual(get_section_type("TUT", norm_text), "TUTR")
        self.assertEqual(get_section_type("TUTR", norm_text), "TUTR")
        self.assertEqual(get_section_type("Tutorial", norm_text), "TUTR")

    def test_seminar_variants(self):
        """Test seminar section type variants."""
        self.assertEqual(get_section_type("SEM", norm_text), "SEMR")
        self.assertEqual(get_section_type("SEMR", norm_text), "SEMR")
        self.assertEqual(get_section_type("Seminar", norm_text), "SEMR")
        self.assertEqual(get_section_type("SEMINAR", norm_text), "SEMR")

    def test_studio(self):
        """Test studio section type."""
        self.assertEqual(get_section_type("STDO", norm_text), "STDO")
        self.assertEqual(get_section_type("Studio", norm_text), "STDO")
        self.assertEqual(get_section_type("STUDIO", norm_text), "STDO")

    def test_blended_learning(self):
        """Test blended learning section type."""
        self.assertEqual(get_section_type("BLEN", norm_text), "BLEN")
        self.assertEqual(get_section_type("Blended", norm_text), "BLEN")
        self.assertEqual(get_section_type("BLENDED", norm_text), "BLEN")

    def test_online_variants(self):
        """Test online section type variants."""
        self.assertEqual(get_section_type("ONL", norm_text), "ONLN")
        self.assertEqual(get_section_type("ONLN", norm_text), "ONLN")
        self.assertEqual(get_section_type("Online", norm_text), "ONLN")
        self.assertEqual(get_section_type("ONLINE", norm_text), "ONLN")
        self.assertEqual(get_section_type("ONCA", norm_text), "ONCA")

    def test_coop_variants(self):
        """Test co-op section type variants."""
        self.assertEqual(get_section_type("COOP", norm_text), "COOP")
        self.assertEqual(get_section_type("Co-op", norm_text), "COOP")
        self.assertEqual(get_section_type("COOPTERM", norm_text), "COOP")
        self.assertEqual(get_section_type("COOPWORKTERM", norm_text), "COOP")

    def test_independent_study_variants(self):
        """Test independent study section type variants."""
        self.assertEqual(get_section_type("ISTY", norm_text), "ISTY")
        self.assertEqual(get_section_type("ind study", norm_text), "ISTY")
        self.assertEqual(get_section_type("INDEPENDENTSTUDY", norm_text), "ISTY")
        self.assertEqual(get_section_type("INDSTUDY", norm_text), "ISTY")
        self.assertEqual(get_section_type("IDS", norm_text), "IDS")
        self.assertEqual(get_section_type("Individual Directed Study", norm_text), "IDS")

    def test_directed_reading(self):
        """Test directed reading section type."""
        self.assertEqual(get_section_type("DIRD", norm_text), "DIRD")
        self.assertEqual(get_section_type("Directed Study", norm_text), "DIRD")
        self.assertEqual(get_section_type("DIRECTEDSTUDY", norm_text), "DIRD")

    def test_field_experience_variants(self):
        """Test field experience section type variants."""
        self.assertEqual(get_section_type("FDEX", norm_text), "FDEX")
        self.assertEqual(get_section_type("Field Exercise", norm_text), "FDEX")
        self.assertEqual(get_section_type("FIELDEXERCISE", norm_text), "FDEX")
        self.assertEqual(get_section_type("FIEL", norm_text), "FIEL")
        self.assertEqual(get_section_type("Field Trip", norm_text), "FIEL")
        self.assertEqual(get_section_type("FIELDWORK", norm_text), "FIEL")

    def test_internship(self):
        """Test internship section type."""
        self.assertEqual(get_section_type("INSP", norm_text), "INSP")
        self.assertEqual(get_section_type("Internship", norm_text), "INSP")
        self.assertEqual(get_section_type("INTERNSHIP", norm_text), "INSP")

    def test_research_variants(self):
        """Test research section type variants."""
        self.assertEqual(get_section_type("RESP", norm_text), "RESP")
        self.assertEqual(get_section_type("Research", norm_text), "RESP")
        self.assertEqual(get_section_type("RESEARCH", norm_text), "RESP")
        self.assertEqual(get_section_type("REEV", norm_text), "REEV")
        self.assertEqual(get_section_type("Research Evaluation", norm_text), "REEV")
        self.assertEqual(get_section_type("RESEARCH EVALUATION", norm_text), "REEV")
        self.assertEqual(get_section_type("ResearchEvaluation", norm_text), "REEV")

    def test_thesis(self):
        """Test thesis section type."""
        self.assertEqual(get_section_type("THES", norm_text), "THES")
        self.assertEqual(get_section_type("Thesis", norm_text), "THES")
        self.assertEqual(get_section_type("THESIS", norm_text), "THES")

    def test_workshop_variants(self):
        """Test workshop section type variants."""
        self.assertEqual(get_section_type("WKSP", norm_text), "WKSP")
        self.assertEqual(get_section_type("Workshop", norm_text), "WKSP")
        self.assertEqual(get_section_type("WORKSHOP", norm_text), "WKSP")
        self.assertEqual(get_section_type("WRKS", norm_text), "WRKS")
        self.assertEqual(get_section_type("WRK", norm_text), "WRKS")

    def test_practicum(self):
        """Test practicum section type."""
        self.assertEqual(get_section_type("PRAC", norm_text), "PRAC")
        self.assertEqual(get_section_type("Practicum", norm_text), "PRAC")
        self.assertEqual(get_section_type("PRA", norm_text), "PRAC")

    def test_clinical(self):
        """Test clinical section type."""
        self.assertEqual(get_section_type("CLIN", norm_text), "CLIN")
        self.assertEqual(get_section_type("Clinical", norm_text), "CLIN")
        self.assertEqual(get_section_type("CLINICAL", norm_text), "CLIN")

    def test_hybrid_flex(self):
        """Test hybrid flex section type."""
        self.assertEqual(get_section_type("HYFX", norm_text), "HYFX")
        self.assertEqual(get_section_type("Hybrid Flex", norm_text), "HYFX")
        self.assertEqual(get_section_type("HYBRIDFLEX", norm_text), "HYFX")

    def test_correspondence(self):
        """Test correspondence section type."""
        self.assertEqual(get_section_type("CORS", norm_text), "CORS")
        self.assertEqual(get_section_type("Correspondence", norm_text), "CORS")
        self.assertEqual(get_section_type("CORRESPONDENCE", norm_text), "CORS")

    def test_dissertation(self):
        """Test dissertation section type."""
        self.assertEqual(get_section_type("DISS", norm_text), "DISS")
        self.assertEqual(get_section_type("Dissertation", norm_text), "DISS")
        self.assertEqual(get_section_type("DISSERTATION", norm_text), "DISS")

    def test_language_classes(self):
        """Test language classes section type."""
        self.assertEqual(get_section_type("LGCL", norm_text), "LGCL")
        self.assertEqual(get_section_type("Language Classes", norm_text), "LGCL")
        self.assertEqual(get_section_type("LANGUAGECLASSES", norm_text), "LGCL")

    def test_performance(self):
        """Test performance section type."""
        self.assertEqual(get_section_type("PERF", norm_text), "PERF")
        self.assertEqual(get_section_type("Performance", norm_text), "PERF")
        self.assertEqual(get_section_type("PERFORMANCE", norm_text), "PERF")

    def test_remote(self):
        """Test remote section type."""
        self.assertEqual(get_section_type("REMT", norm_text), "REMT")
        self.assertEqual(get_section_type("Remote", norm_text), "REMT")
        self.assertEqual(get_section_type("REMOTE", norm_text), "REMT")

    def test_review_paper(self):
        """Test review paper section type."""
        self.assertEqual(get_section_type("REVP", norm_text), "REVP")
        self.assertEqual(get_section_type("Review Paper", norm_text), "REVP")
        self.assertEqual(get_section_type("REVIEWPAPER", norm_text), "REVP")

    def test_no_match(self):
        """Test that unknown section types return empty string."""
        self.assertEqual(get_section_type("unknown", norm_text), "")
        self.assertEqual(get_section_type("XYZ", norm_text), "")
        self.assertEqual(get_section_type("", norm_text), "")
        self.assertEqual(get_section_type("   ", norm_text), "")

    def test_case_insensitivity(self):
        """Test that section type matching is case insensitive."""
        self.assertEqual(get_section_type("lec", norm_text), "LECT")
        self.assertEqual(get_section_type("LEC", norm_text), "LECT")
        self.assertEqual(get_section_type("Lec", norm_text), "LECT")
        self.assertEqual(get_section_type("LeCt", norm_text), "LECT")

    def test_with_spaces_and_special_chars(self):
        """Test that section types work with spaces and special characters."""
        self.assertEqual(get_section_type("  LEC  ", norm_text), "LECT")
        self.assertEqual(get_section_type("Field Exercise", norm_text), "FDEX")
        self.assertEqual(get_section_type("Co-op", norm_text), "COOP")
        self.assertEqual(get_section_type("Research Evaluation", norm_text), "REEV")

    def test_all_mappings_exist(self):
        """Test that all canonical types from the official list are present."""
        official_types = {
            "BLEN", "CLIN", "CORS", "DIRD", "DISS", "FDEX", "FIEL",
            "HYFX", "IDS", "INSP", "ISTY", "LAB", "LECT", "LGCL",
            "ONCA", "ONLN", "PERF", "PRAC", "REEV", "REMT", "RESP",
            "REVP", "SEMR", "STDO", "THES", "TUTR", "WKSP"
        }
        
        # Extract normalized types from mappings
        normalized_types = {mapping[1] for mapping in SECTION_TYPE_MAPPINGS}
        
        # Check that all official types are present
        missing = official_types - normalized_types
        self.assertEqual(missing, set(), f"Missing section types: {missing}")

    def test_first_match_priority(self):
        """Test that first matching pattern takes priority (for overlapping patterns)."""
        # "WORKSHOP" should match "WKSP" mapping due to the ordering
        self.assertEqual(get_section_type("WORKSHOP", norm_text), "WKSP")


if __name__ == "__main__":
    unittest.main()

