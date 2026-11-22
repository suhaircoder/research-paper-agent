"""Checks for the practice papers and a shared-dataset comparison."""

import unittest

from research_paper.compare import compare_briefs
from research_paper.library import load_records, notes_markdown, record_from_brief, save_records
from research_paper.read import join_glyphs
from research_paper.samples import MORPH_NET, SYNC_FACE
from research_paper.service import brief_from_text


class PaperTests(unittest.TestCase):
    def test_syncface_brief(self):
        brief = brief_from_text(SYNC_FACE)
        self.assertIn("SyncFace", brief.method)
        self.assertEqual(brief.datasets, ["HDTF", "VoxCeleb2"])
        self.assertIn(("FID", "14.2"), brief.metrics)
        self.assertIn(("LSE-D", "7.1"), brief.metrics)
        self.assertIn(("Accuracy", "91.4%"), brief.metrics)
        self.assertIn("head turns", brief.limitation)

    def test_morphnet_uses_a_different_number(self):
        brief = brief_from_text(MORPH_NET)
        self.assertIn("3D morphable model", brief.method)
        self.assertEqual(brief.datasets, ["NoW", "Florence"])
        self.assertEqual(brief.metrics, [("NME", "1.8")])
        self.assertIn("mouth", brief.limitation)

    def test_two_papers_do_not_share_data_or_numbers(self):
        left = brief_from_text(SYNC_FACE)
        right = brief_from_text(MORPH_NET)
        comparison = compare_briefs(left, right)
        self.assertEqual(comparison.shared_datasets, [])
        self.assertEqual(comparison.metric_rows, [])
        self.assertIn("different data", comparison.summary)
        self.assertIn("do not report the same number", comparison.summary)

    def test_shared_dataset_is_reported(self):
        other = SYNC_FACE.replace(
            "We evaluate on HDTF and VoxCeleb2.",
            "We evaluate on HDTF and MEAD.",
        ).replace("The FID is 14.2", "The FID is 18.0")
        left = brief_from_text(SYNC_FACE)
        right = brief_from_text(other)
        comparison = compare_briefs(left, right)
        self.assertIn("HDTF", comparison.shared_datasets)
        self.assertEqual(comparison.metric_rows[0][0], "FID")
        self.assertEqual(comparison.metric_rows[0][1:], ("14.2", "18.0"))

    def test_journal_pdf_headings_keep_method_and_data(self):
        paper = """
Article
Heart Disease Prediction with a Stacking Model
A. Author 1
Abstract: Heart disease is hard to detect early. We proposed a stacking model named NCDG for that task.
Keywords: heart disease; stacking
1. Introduction
Early detection matters.
2. Related Work
Other models use the Cleveland dataset.
3. Material and Methods for Heart Disease Prediction
A single classifier is not enough. Details follow.
4. Proposed Methodology for Heart Disease Prediction
Our proposed stacking model contains Naive Bayes and a decision tree, with gradient boosting as the meta learner.
4.2. Heart Disease Dataset Description
To detect HD, the Personal Key Indicators of HD Dataset is used. It has 319795 rows.
5. Results and Discussion of Proposed Models
The model reaches an accuracy of 91% and an F1-Score of 91%.
6. Conclusions
The stacking model is accurate. CatBoost performs best in the meta layer.
Author Contributions: Editing.
"""
        brief = brief_from_text(paper)
        self.assertIn("Heart Disease Prediction", brief.title)
        self.assertIn("hard to detect", brief.problem)
        self.assertIn("stacking model", brief.method)
        self.assertIn("Naive Bayes", brief.method)
        self.assertIn("Personal Key Indicators of HD Dataset", brief.datasets)
        self.assertIn(("Accuracy", "91%"), brief.metrics)
        self.assertNotIn("disclaim", brief.limitation.lower())

    def test_spaced_glyphs_become_words(self):
        glyphs = [
            (10, 0, "B", 12, 20),
            (10, 12, "i", 5, 20),
            (10, 17, "r", 8, 20),
            (10, 25, "d", 10, 20),
            (10, 42, "d", 10, 20),
            (10, 52, "a", 10, 20),
            (10, 62, "t", 8, 20),
            (10, 70, "a", 10, 20),
        ]
        self.assertEqual(join_glyphs(glyphs), "Bird data")

    def test_proposal_without_a_method_heading(self):
        paper = """
1. Introduction
Automated bird detection has been an active research area. Occlusion makes small birds hard to see.
1.3 Research Objective
The main objective of this study is to develop a robust deep learning framework for occluded birds.
2. Literature review
On VisDrone2019, a model achieved 44.41% mAP@50. DOTA and UAVDT are used for aerial detection.
However, reliable detection of highly occluded birds remains difficult.
"""
        brief = brief_from_text(paper)
        self.assertIn("bird detection", brief.problem)
        self.assertIn("deep learning framework", brief.method)
        self.assertIn("VisDrone2019", brief.datasets)
        self.assertIn("DOTA", brief.datasets)
        self.assertIn("UAVDT", brief.datasets)
        self.assertEqual(brief.metrics, [])
        self.assertNotIn("44.41", brief.limitation)

    def test_library_keeps_each_paper_once(self):
        folder = self._library_path()
        first = record_from_brief(brief_from_text(SYNC_FACE))
        second = record_from_brief(brief_from_text(MORPH_NET))
        save_records([first], folder)
        saved = save_records([first, second], folder)
        self.assertEqual([item["title"] for item in saved], [first["title"], second["title"]])
        self.assertEqual(len(load_records(folder)), 2)
        notes = notes_markdown(saved)
        self.assertIn("HDTF", notes)
        self.assertIn("head turns", notes)
        self.assertIn("| Paper | Data | Numbers |", notes)

    def _library_path(self):
        import tempfile
        from pathlib import Path

        folder = Path(tempfile.mkdtemp())
        return folder / "papers.json"


if __name__ == "__main__":
    unittest.main()
