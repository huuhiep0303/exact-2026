import unittest

from app.config import config
from app.modules.answer_target import detect_answer_target
from app.modules.premise_filter import filter_premises
from app.modules.rag import retrieve_premises
from app.modules.topic_router import detect_topic


class PremiseFilterTests(unittest.TestCase):
    def setUp(self):
        import app.modules.knowledge_base as kb_module

        self.previous_use_qdrant = config.use_qdrant
        config.use_qdrant = False
        kb_module._kb_instance = None

    def tearDown(self):
        import app.modules.knowledge_base as kb_module

        config.use_qdrant = self.previous_use_qdrant
        kb_module._kb_instance = None

    def _retrieve_and_filter(self, question: str, topic: str):
        target = detect_answer_target(question)
        premises, _ = retrieve_premises(question, top_k=5, topic=topic)
        return target, filter_premises(question, topic=topic, intent=target.intent, premises=premises)

    def test_round2_parallel_capacitor_rejects_merging(self):
        question = "Two identical capacitors C = 6 uF are connected in parallel. What is the equivalent capacitance?"
        target, result = self._retrieve_and_filter(question, "capacitor")

        self.assertEqual(target.intent, "equivalent_capacitance_parallel")
        self.assertTrue(any("parallel" in p.lower() for p in result.applicable), result.applicable)
        self.assertTrue(any("merging" in p.lower() for p in result.rejected), result.rejected)

    def test_round2_series_capacitor_rejects_merging(self):
        question = "Two identical capacitors C = 6 uF are connected in series. What is the equivalent capacitance?"
        target, result = self._retrieve_and_filter(question, "capacitor")

        self.assertEqual(target.intent, "equivalent_capacitance_series")
        self.assertTrue(any("series" in p.lower() for p in result.applicable), result.applicable)
        self.assertTrue(any("merging" in p.lower() for p in result.rejected), result.rejected)

    def test_hidden_general_intents_reject_wrong_topic_premises(self):
        cases = [
            (
                "A gas expands at constant pressure. Its volume changes by 0.2 m^3 under pressure 100000 Pa. Find the work done.",
                "general",
                "work_energy",
            ),
            (
                "A convex lens has focal length 10 cm and an object is 30 cm away. Find the image distance.",
                "general",
                "thin_lens",
            ),
            (
                "A wave has frequency 50 Hz and wavelength 2 m. Find its speed.",
                "general",
                "wave_speed",
            ),
            (
                "A spring with k = 200 N/m is compressed by 0.1 m. Find the elastic energy.",
                "general",
                "elastic_energy",
            ),
            (
                "A body of mass 2 kg accelerates at 3 m/s^2. Find the force.",
                "general",
                "force_ma",
            ),
        ]

        for question, topic, expected_intent in cases:
            with self.subTest(question=question):
                detected_topic = detect_topic(question)
                self.assertEqual(detected_topic, topic)
                target, result = self._retrieve_and_filter(question, detected_topic)
                self.assertEqual(target.intent, expected_intent)
                joined = "\n".join(result.applicable).lower()
                self.assertNotIn("coulomb", joined)
                self.assertNotIn("resonance", joined)
                self.assertNotIn("solenoid", joined)
                self.assertNotIn("point where v = 0", joined)

    def test_lc_energy_current_percentage_does_not_route_to_electric_field(self):
        question = (
            "In an oscillating LC circuit, when the electric field energy is 1/4 of the total energy, "
            "what percentage (%) of the maximum current is the instantaneous current?"
        )
        detected_topic = detect_topic(question)
        self.assertEqual(detected_topic, "energy_oscillation")

        target, result = self._retrieve_and_filter(question, detected_topic)
        self.assertEqual(target.intent, "lc_current_percentage_from_energy")
        self.assertEqual(target.quantity, "percentage")
        joined = "\n".join(result.applicable).lower()
        self.assertNotIn("point charge", joined)
        self.assertNotIn("coulomb", joined)


if __name__ == "__main__":
    unittest.main()
