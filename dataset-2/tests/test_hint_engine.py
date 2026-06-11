import unittest
import csv
from pathlib import Path

from app.hints import get_topic_hints, get_unit_hints
from app.modules.topic_router import detect_topic
from app.prompts.reasoner_prompt import build_reasoner_prompt


DATASET = Path(__file__).resolve().parents[1] / "dataset_2" / "Physics_Problems_Text_Only.csv"


def _dataset_question(sample_id: str) -> str:
    with DATASET.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row["id"] == sample_id:
                return row["question"]
    raise AssertionError(f"Missing dataset id {sample_id}")


class HintEngineTests(unittest.TestCase):
    def test_unit_conversion_hints_cover_common_units(self):
        question = "Find energy 30 mJ for C = 100 μF, r = 8 cm, f = 2 kHz, q = 5 nC."

        hints = get_unit_hints(question)
        text = "\n".join(hints)

        self.assertIn("μF", text)
        self.assertIn("cm", text)
        self.assertIn("mJ", text)
        self.assertIn("kHz", text)
        self.assertIn("nC", text)

    def test_topic_hints_cover_ld_geometry_patterns(self):
        equilateral = get_topic_hints(
            "Three charges are placed at the vertices of an equilateral triangle.",
            "coulomb_force",
        )
        right_triangle = get_topic_hints(
            "Triangle ABC is right-angled at A with AB = 3 cm and BC = 5 cm.",
            "coulomb_force",
        )
        bisector = get_topic_hints(
            "Two charges are 8 cm apart. Point M is on the perpendicular bisector 3 cm from AB.",
            "coulomb_force",
        )

        self.assertTrue(any("equilateral" in hint.lower() for hint in equilateral))
        self.assertTrue(any("right-angled" in hint.lower() for hint in right_triangle))
        self.assertTrue(any("perpendicular bisector" in hint.lower() for hint in bisector))

    def test_topic_hints_cover_capacitor_source_state(self):
        disconnected = get_topic_hints(
            "A charged capacitor is then disconnected from the source and the distance is doubled.",
            "capacitor",
        )
        connected = get_topic_hints(
            "A capacitor remains connected to the source while the plate distance is doubled.",
            "capacitor",
        )

        self.assertTrue(any("DISCONNECTED" in hint for hint in disconnected))
        self.assertTrue(any("CONNECTED" in hint for hint in connected))

    def test_topic_hints_cover_chlt_yes_no_resonance(self):
        hints = get_topic_hints(
            "Is the RLC circuit at resonance when f = 50 Hz?",
            "ac_circuit",
        )

        self.assertTrue(any("YES/NO" in hint for hint in hints))
        self.assertTrue(any("'Yes' or 'No'" in hint for hint in hints))

    def test_topic_hints_cover_measurement_error(self):
        hints = get_topic_hints(
            "Find the random error and percentage error for multiple measurements with least count.",
            "measurement_error",
        )
        text = "\n".join(hints)

        self.assertIn("LCNS", text)
        self.assertIn("MAXIMUM deviation", text)
        self.assertIn("Percentage error", text)

    def test_topic_hints_cover_dt_ddt_nl(self):
        dt = get_topic_hints(
            "Find the electric potential at M due to two point charges.",
            "electric_potential",
        )
        ddt = get_topic_hints(
            "How does the magnetic field of a solenoid change when current is doubled?",
            "magnetism_induction",
        )
        nl = get_topic_hints(
            "In an LC oscillation, when capacitor energy and inductor energy are equal.",
            "energy_oscillation",
        )

        self.assertTrue(any("POTENTIAL IS SCALAR" in hint for hint in dt))
        self.assertTrue(any("QUALITATIVE ANSWER" in hint for hint in ddt))
        self.assertTrue(any("W_C = W_L" in hint for hint in nl))

    def test_router_and_hints_cover_known_regression_groups(self):
        expected_topics = {
            "NL001": "energy_oscillation",
            "NL003": "energy_oscillation",
            "LD008": "coulomb_force",
            "LD009": "coulomb_force",
            "LD015": "coulomb_force",
            "LD019": "coulomb_force",
            "DT002": "coulomb_force",
            "DT003": "coulomb_force",
            "DT007": "coulomb_force",
            "THCB066": "dc_circuit",
            "THCB074": "dc_circuit",
            "CHLT010": "ac_circuit",
            "CHLT013": "ac_circuit",
            "CHLT014": "ac_circuit",
            "CHLT016": "ac_circuit",
            "CHLT019": "ac_circuit",
            "DDT321": "ac_circuit",
        }

        for sample_id, expected_topic in expected_topics.items():
            with self.subTest(sample_id=sample_id):
                question = _dataset_question(sample_id)
                topic = detect_topic(question)
                hints = get_topic_hints(question, topic)

                self.assertEqual(topic, expected_topic)
                self.assertTrue(hints, f"{sample_id} produced no hints")

        for sample_id in ["CHLT010", "CHLT013", "CHLT014", "CHLT016", "CHLT019"]:
            with self.subTest(yes_no=sample_id):
                question = _dataset_question(sample_id)
                hints = get_topic_hints(question, detect_topic(question))
                self.assertTrue(any("YES/NO" in hint for hint in hints), hints)

    def test_reasoner_prompt_separates_unit_and_topic_hints(self):
        prompt = build_reasoner_prompt(
            question="Find energy for C = 100 μF in an LC circuit.",
            premises=["Energy stored: W = 1/2*C*U^2"],
            topic="energy_oscillation",
            question_type="quantitative",
            unit_hints=["Unit: 1 μF = 1e-06 F"],
            geometry_hints=["LC ENERGY CONSERVATION: W_total = constant"],
        )

        self.assertIn("Unit conversion facts", prompt)
        self.assertIn("Topic/geometry hints", prompt)
        self.assertLess(
            prompt.index("Unit: 1 μF = 1e-06 F"),
            prompt.index("LC ENERGY CONSERVATION"),
        )

    def test_dt_hard_hints_cover_vector_regressions(self):
        midpoint_question = _dataset_question("DT001")
        zero_field_question = _dataset_question("DT025")
        square_question = _dataset_question("DT020")

        midpoint = get_topic_hints(midpoint_question, detect_topic(midpoint_question))
        zero_field = get_topic_hints(zero_field_question, detect_topic(zero_field_question))
        square = get_topic_hints(square_question, detect_topic(square_question))

        self.assertTrue(any("HARD SYMMETRY" in hint for hint in midpoint), midpoint)
        self.assertTrue(any("V=0" in hint for hint in zero_field), zero_field)
        self.assertTrue(any("HARD ZERO-FIELD REGION" in hint and "outside" in hint for hint in zero_field), zero_field)
        self.assertTrue(any("HARD SQUARE SIGN CHECK" in hint for hint in square), square)
        self.assertTrue(any("HARD SYMBOLIC" in hint for hint in square), square)

    def test_symbolic_input_units_are_not_output_units(self):
        hints = get_unit_hints(_dataset_question("DT020"))
        joined = "\n".join(hints)

        self.assertNotIn("OUTPUT UNIT REQUIRED", joined)
        self.assertNotIn("unit 'm'", joined)


if __name__ == "__main__":
    unittest.main()
