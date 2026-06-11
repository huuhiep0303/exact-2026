import json
import unittest
from pathlib import Path

from app.config import config
from app.modules.knowledge_base import InMemoryKB
from app.modules.rag import retrieve_premises


class KnowledgeBaseExpansionTests(unittest.TestCase):
    def test_structured_laws_have_answer_type(self):
        data = json.loads(Path(config.kb_path).read_text(encoding="utf-8"))
        kb_data = data.get("knowledge_base", data)
        laws = [
            law
            for topic in kb_data.get("topics", [])
            for law in topic.get("laws", [])
        ]

        self.assertGreaterEqual(len(laws), 79)
        self.assertTrue(all(law.get("answer_type") for law in laws))

    def test_reference_docs_expand_kb_to_plan_floor(self):
        kb = InMemoryKB()
        count = kb.load_from_json(config.kb_path)

        self.assertGreaterEqual(count, 300)

    def test_answer_type_is_searchable_and_returned_in_premise(self):
        kb = InMemoryKB()
        kb.load_from_json(config.kb_path)

        results = kb.search("electric potential scalar superposition", top_k=3)
        self.assertTrue(results)
        self.assertTrue(any(entry.answer_type for entry, _ in results))
        self.assertTrue(any("Answer type:" in entry.premise_string for entry, _ in results))

    def test_reference_docs_improve_topic_specific_retrieval(self):
        kb = InMemoryKB()
        kb.load_from_json(config.kb_path)

        queries = {
            "LCNS random error": "THCB",
            "Is RLC circuit at resonance Yes No": "CHLT",
            "capacitor disconnected distance doubled": "TD",
        }

        for query, expected_prefix in queries.items():
            with self.subTest(query=query):
                results = kb.search(query, top_k=3)
                self.assertTrue(
                    any(entry.topic_prefix == expected_prefix for entry, _ in results),
                    [entry.topic_prefix for entry, _ in results],
                )

    def test_hybrid_retrieval_returns_intent_specific_premises(self):
        import app.modules.knowledge_base as kb_module

        previous_use_qdrant = config.use_qdrant
        config.use_qdrant = False
        kb_module._kb_instance = None
        try:
            cases = [
                (
                    "A voltage source of U = 9V. Two lamps are connected in parallel, each with R = 9Ω. Calculate current.",
                    "dc_circuit",
                    "parallel",
                ),
                (
                    "A capacitor with C = 20 μF is charged to 100 V. Calculate the energy in mJ.",
                    "energy_oscillation",
                    "energy",
                ),
                (
                    "Two electric forces of 3 N and 4 N act in the same direction. Find the resultant force.",
                    "coulomb_force",
                    "same direction",
                ),
                (
                    "Two charges q1 = q2 = q are separated by AB = 2a. Point M is on the perpendicular bisector at distance h. Find the electric field at M.",
                    "coulomb_force",
                    "perpendicular bisector",
                ),
                (
                    "Find the point where the net electric field is zero for q1 and q2 on a line.",
                    "electric_field_zero",
                    "zero electric field",
                ),
                (
                    "Two charges q1 and q2 create an electric field at C. Calculate the force on q3 placed at C.",
                    "coulomb_force",
                    "force on a test charge",
                ),
            ]

            for question, topic, expected_text in cases:
                with self.subTest(topic=topic):
                    premises, score = retrieve_premises(question, top_k=3, topic=topic)
                    joined = "\n".join(premises).lower()
                    self.assertGreater(score, 0.0)
                    self.assertIn(expected_text, joined)
        finally:
            config.use_qdrant = previous_use_qdrant
            kb_module._kb_instance = None

    def test_dt_electric_field_retrieval_avoids_zero_potential_for_zero_field(self):
        import app.modules.knowledge_base as kb_module

        previous_use_qdrant = config.use_qdrant
        config.use_qdrant = False
        kb_module._kb_instance = None
        try:
            premises, score = retrieve_premises(
                "Given q1 = -9e-6 C and q2 = 4e-6 C separated by 20 cm, find where the net electric field is zero.",
                top_k=3,
                topic="electric_field_zero",
            )
            joined = "\n".join(premises).lower()
            self.assertGreater(score, 0.0)
            self.assertIn("zero electric field", joined)
            self.assertNotIn("zero-potential", joined)
            self.assertNotIn("point where v = 0", joined)
        finally:
            config.use_qdrant = previous_use_qdrant
            kb_module._kb_instance = None

    def test_dt_vector_regression_retrieval_uses_geometry_intent(self):
        import app.modules.knowledge_base as kb_module

        previous_use_qdrant = config.use_qdrant
        config.use_qdrant = False
        kb_module._kb_instance = None
        try:
            cases = [
                (
                    "Two point charges are separated by 10 cm. q1 = q2 = 16 x 10^-8 C. Find electric field at M where MA = MB = 5 cm.",
                    "coulomb_force",
                    "midpoint symmetry",
                    "perpendicular bisector equal",
                ),
                (
                    "q1 = q2 = 16 x 10^-8 C are at A and B, 10 cm apart. Find electric field at N where NA = 5 cm and NB = 15 cm.",
                    "coulomb_force",
                    "collinear",
                    "perpendicular bisector equal",
                ),
                (
                    "q1 = -12 x 10^-6 C and q2 = 2.5 x 10^-6 C are at A and B, 15 cm apart. Find point M where net electric field is zero. Calculate AM.",
                    "electric_field_zero",
                    "opposite",
                    "point where v = 0",
                ),
                (
                    "Four charges of magnitude q are at square ABCD side length a. Positive charges at A and D, negative charges at B and C. Determine field at intersection of diagonals.",
                    "coulomb_force",
                    "square",
                    "midpoint symmetry",
                ),
            ]

            for question, topic, expected_text, forbidden_text in cases:
                with self.subTest(expected_text=expected_text):
                    premises, score = retrieve_premises(question, top_k=3, topic=topic)
                    joined = "\n".join(premises).lower()
                    self.assertGreater(score, 0.0)
                    self.assertIn(expected_text, joined)
                    self.assertNotIn(forbidden_text, joined)
        finally:
            config.use_qdrant = previous_use_qdrant
            kb_module._kb_instance = None


if __name__ == "__main__":
    unittest.main()
