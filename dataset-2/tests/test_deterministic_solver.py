import csv
import unittest
from pathlib import Path

from app.modules.deterministic_solver import solve_deterministic
from evaluate_pipeline import compare_prediction


DATASET = Path("dataset_2/Physics_Problems_Text_Only.csv")


class DeterministicSolverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with DATASET.open("r", encoding="utf-8-sig", newline="") as f:
            cls.rows = {row["id"]: row for row in csv.DictReader(f)}

    def assert_solver_matches(self, sample_id: str):
        row = self.rows[sample_id]
        result = solve_deterministic(row["question"])
        self.assertIsNotNone(result, sample_id)
        final = f"{result.answer} {result.unit}".strip()
        comparison = compare_prediction(final, row["answer"], row["unit"], 1e-2, 1e-9)
        self.assertTrue(comparison[4], f"{sample_id}: {final} != {row['answer']} {row['unit']}")

    def assert_topic_solver_matches(self, sample_id: str, topic: str):
        row = self.rows[sample_id]
        result = solve_deterministic(row["question"], topic=topic)
        self.assertIsNotNone(result, sample_id)
        final = f"{result.answer} {result.unit}".strip()
        comparison = compare_prediction(final, row["answer"], row["unit"], 1e-2, 1e-9)
        self.assertTrue(comparison[4], f"{sample_id}: {final} != {row['answer']} {row['unit']}")

    def test_direct_coulomb_force_round1_regression(self):
        question = (
            "Two point charges q1 = +3.0 \u03bcC and q2 = -5.0 \u03bcC are "
            "separated by a distance of 0.30 m in air. Calculate the magnitude "
            "of the electrostatic force between them. Use k = 9.0 \u00d7 10^9 "
            "N\u00b7m\u00b2/C\u00b2."
        )
        result = solve_deterministic(question, topic="coulomb_force")
        self.assertIsNotNone(result)
        self.assertEqual(result.answer, "1.5")
        self.assertEqual(result.unit, "N")
        self.assertEqual(result.strategy, "ld_direct_coulomb_force")

    def test_midpoint_electric_field_round1_regression(self):
        question = (
            "Two charges +4.0 nC and -4.0 nC are fixed 20 cm apart in air. "
            "Calculate the magnitude of the electric field at the midpoint "
            "between the charges. Use k = 9.0 \u00d7 10^9 N\u00b7m\u00b2/C\u00b2."
        )
        result = solve_deterministic(question, topic="coulomb_force")
        self.assertIsNotNone(result)
        self.assertEqual(result.answer, "7200")
        self.assertEqual(result.unit, "V/m")
        self.assertEqual(result.strategy, "ld_midpoint_field")

    def test_series_capacitor_charge_round1_regression(self):
        question = (
            "Two capacitors C1 = 6.0 \u03bcF and C2 = 3.0 \u03bcF are connected "
            "in series across an 18 V battery. Calculate the charge stored on "
            "each capacitor."
        )
        result = solve_deterministic(question, topic="capacitor")
        self.assertIsNotNone(result)
        self.assertEqual(result.answer, "36")
        self.assertEqual(result.unit, "\u03bcC")
        self.assertEqual(result.strategy, "td_series_capacitor_charge")

    def test_thin_lens_image_distance_round1_regression(self):
        question = (
            "An object is placed 30 cm in front of a converging lens with "
            "focal length 20 cm. Calculate the image distance."
        )
        result = solve_deterministic(question, topic="general")
        self.assertIsNotNone(result)
        self.assertEqual(result.answer, "60")
        self.assertEqual(result.unit, "cm")
        self.assertEqual(result.strategy, "optics_thin_lens_image_distance")

    def test_resistor_energy_round1_regression(self):
        question = (
            "A 24 \u03a9 resistor is connected to a 12 V battery for 5 minutes. "
            "Calculate the electrical energy converted in the resistor."
        )
        result = solve_deterministic(question, topic="general")
        self.assertIsNotNone(result)
        self.assertEqual(result.answer, "1800")
        self.assertEqual(result.unit, "J")
        self.assertEqual(result.strategy, "general_resistor_electrical_energy")

    def test_conductor_resistivity_round1_regression(self):
        question = (
            "A conductor has length l = 2 m, cross-sectional area S = 1 mm^2, "
            "and resistivity rho = 0.5 ohm*mm^2/m. Calculate its resistance."
        )
        result = solve_deterministic(question, topic="general")
        self.assertIsNotNone(result)
        self.assertEqual(result.answer, "1")
        self.assertEqual(result.unit, "ohm")
        self.assertEqual(result.strategy, "general_conductor_resistance_from_resistivity")

    def test_ideal_gas_pressure_round1_regression(self):
        question = (
            "A gas sample contains n = 0.50 mol at temperature T = 300 K in "
            "a volume V = 0.010 m^3. Calculate the pressure of the gas. "
            "Use R = 8.314 J/(mol*K)."
        )
        result = solve_deterministic(question, topic="general")
        self.assertIsNotNone(result)
        self.assertEqual(result.answer, "125000")
        self.assertEqual(result.unit, "Pa")
        self.assertEqual(result.strategy, "general_ideal_gas_pressure")

    def test_two_charge_potential_round1_regression(self):
        question = (
            "A point P is 10 cm from a charge q1 = +6.0 nC and 20 cm from "
            "a charge q2 = -2.0 nC. Calculate the electric potential at P. "
            "Use k = 9.0 x 10^9 N*m^2/C^2."
        )
        result = solve_deterministic(question, topic="electric_potential")
        self.assertIsNotNone(result)
        self.assertEqual(result.answer, "450")
        self.assertEqual(result.unit, "V")
        self.assertEqual(result.strategy, "dt_two_charge_potential_at_point")

    def test_single_charge_electric_field_round2_regression(self):
        question = (
            "A point charge q = 4 nC creates an electric field at distance "
            "r = 0.20 m. Use k = 9e9. Calculate the field magnitude."
        )
        result = solve_deterministic(question, topic="coulomb_force")
        self.assertIsNotNone(result)
        self.assertEqual(result.answer, "900")
        self.assertEqual(result.unit, "N/C")
        self.assertEqual(result.strategy, "dt_single_charge_electric_field")

    def test_series_resistor_current_round1_regression(self):
        question = (
            "Two resistors R1 = 12 ohm and R2 = 18 ohm are connected in "
            "series to a 15 V source. Calculate the current in the circuit."
        )
        result = solve_deterministic(question, topic="dc_circuit")
        self.assertIsNotNone(result)
        self.assertEqual(result.answer, "0.5")
        self.assertEqual(result.unit, "A")
        self.assertEqual(result.strategy, "thcb_series_resistor_current")

    def test_parallel_resistor_total_current_round1_regression(self):
        question = (
            "Two resistors R1 = 6 ohm and R2 = 3 ohm are connected in "
            "parallel across a 12 V source. Calculate the total current drawn "
            "from the source."
        )
        result = solve_deterministic(question, topic="dc_circuit")
        self.assertIsNotNone(result)
        self.assertEqual(result.answer, "6")
        self.assertEqual(result.unit, "A")
        self.assertEqual(result.strategy, "thcb_parallel_total_current")

    def test_work_energy_final_speed_round1_regression(self):
        question = (
            "A 2.0 kg object starts from rest. A constant net force of 10 N "
            "acts on it over a distance of 5.0 m. Calculate the final speed "
            "of the object."
        )
        result = solve_deterministic(question, topic="general")
        self.assertIsNotNone(result)
        self.assertEqual(result.answer, "7.07107")
        self.assertEqual(result.unit, "m/s")
        self.assertEqual(result.strategy, "general_work_energy_final_speed")

    def test_uniform_braking_distance_round1_regression(self):
        question = (
            "A car moving at 20 m/s brakes uniformly to rest with acceleration "
            "-4.0 m/s^2. Calculate the braking distance."
        )
        result = solve_deterministic(question, topic="general")
        self.assertIsNotNone(result)
        self.assertEqual(result.answer, "50")
        self.assertEqual(result.unit, "m")
        self.assertEqual(result.strategy, "general_uniform_braking_distance")

    def test_elevator_normal_force_round1_regression(self):
        question = (
            "A person of mass 60 kg stands in an elevator accelerating upward "
            "at 1.5 m/s^2. Calculate the normal force exerted by the elevator "
            "floor on the person. Use g = 9.8 m/s^2."
        )
        result = solve_deterministic(question, topic="general")
        self.assertIsNotNone(result)
        self.assertEqual(result.answer, "678")
        self.assertEqual(result.unit, "N")
        self.assertEqual(result.strategy, "general_elevator_normal_force")

    def test_vertical_throw_max_height_round1_regression(self):
        question = (
            "A ball is thrown vertically upward with an initial speed of "
            "19.6 m/s. Calculate the maximum height reached by the ball. "
            "Use g = 9.8 m/s^2."
        )
        result = solve_deterministic(question, topic="general")
        self.assertIsNotNone(result)
        self.assertEqual(result.answer, "19.6")
        self.assertEqual(result.unit, "m")
        self.assertEqual(result.strategy, "general_vertical_throw_max_height")

    def test_constant_acceleration_round1_regression(self):
        question = (
            "A car starts with an initial speed of 8 m/s and travels 66 m "
            "in 6 s with constant acceleration. Calculate the acceleration "
            "of the car."
        )
        result = solve_deterministic(question, topic="general")
        self.assertIsNotNone(result)
        self.assertEqual(result.answer, "1")
        self.assertEqual(result.unit, "m/s^2")
        self.assertEqual(result.strategy, "general_constant_acceleration_from_distance")

    def test_transformer_secondary_voltage_round1_regression(self):
        question = (
            "A transformer has primary turns N1 = 200, secondary turns "
            "N2 = 800, and primary voltage U1 = 12 V. Calculate the "
            "secondary voltage."
        )
        result = solve_deterministic(question, topic="general")
        self.assertIsNotNone(result)
        self.assertEqual(result.answer, "48")
        self.assertEqual(result.unit, "V")
        self.assertEqual(result.strategy, "general_transformer_secondary_voltage")

    def test_dt_regression_cases(self):
        for sample_id in [
            "DT002",
            "DT003",
            "DT004",
            "DT005",
            "DT006",
            "DT007",
            "DT008",
            "DT019",
            "DT020",
            "DT025",
            "DT029",
            "DT033",
            "DT035",
        ]:
            with self.subTest(sample_id=sample_id):
                self.assert_solver_matches(sample_id)

    def test_low_topic_formula_regression_cases(self):
        for sample_id in [
            "TD001",
            "TD002",
            "TD003",
            "TD004",
            "TD005",
            "TD007",
            "TD008",
            "TD009",
            "TD011",
            "TD015",
            "TD016",
            "TD017",
            "TD018",
            "TD030",
            "THCB003",
            "THCB008",
            "THCB076",
            "THCB086",
            "THCB087",
            "THCB088",
            "THCB090",
            "THCB101",
            "THCB118",
            "THCB130",
            "THCB066",
            "THCB068",
            "THCB070",
            "THCB072",
            "THCB075",
            "DDT131",
            "DDT134",
            "DDT139",
            "DDT143",
            "DDT146",
            "DDT149",
            "LD001",
            "LD004",
            "LD005",
            "LD006",
            "LD007",
            "LD010",
            "LD012",
            "LD014",
            "LD018",
            "LD024",
            "LD025",
            "LD026",
            "LD030",
            "LD031",
            "LD032",
            "LD033",
            "LD034",
            "LD035",
            "LD037",
            "LD038",
            "DDT157",
            "DDT158",
            "DDT203",
            "DDT204",
            "DDT209",
            "CH021",
            "CH022",
            "CH025",
            "CH061",
            "DDT219",
            "DDT321",
            "DDT331",
            "DDT340",
        ]:
            with self.subTest(sample_id=sample_id):
                self.assert_solver_matches(sample_id)

    def test_chlt_resonance_yes_no_regression_cases(self):
        for sample_id in ["CHLT003", "CHLT004", "CHLT010", "CHLT014"]:
            with self.subTest(sample_id=sample_id):
                self.assert_topic_solver_matches(sample_id, "CHLT")

    def test_final_pre_finetune_solver_regression_cases(self):
        for sample_id in [
            "CH027",
            "CH066",
            "NL311",
            "NL330",
            "DT040",
            "DT048",
            "DT072",
            "LD302",
            "LD312",
            "LD338",
        ]:
            with self.subTest(sample_id=sample_id):
                topic = "".join(ch for ch in sample_id if not ch.isdigit())
                self.assert_topic_solver_matches(sample_id, topic)

    def test_round1_hidden_regression_cases(self):
        samples = [
            (
                "Two charges +4.0 nC and -4.0 nC are fixed 20 cm apart in air. Calculate the magnitude of the electric field at the midpoint between the charges. Use k = 9.0 × 10^9 N·m²/C².",
                "7200",
                "V/m",
                "ld_midpoint_field",
            ),
            (
                "A point P is 10 cm from a charge q1 = +6.0 nC and 20 cm from a charge q2 = -2.0 nC. Calculate the electric potential at P. Use k = 9.0 × 10^9 N·m²/C².",
                "450",
                "V",
                "dt_two_charge_potential_at_point",
            ),
            (
                "An LC circuit has inductance L = 0.20 H and capacitance C = 50 μF. Calculate the resonant frequency of the circuit.",
                "50.329",
                "Hz",
                "rlc_resonant_frequency",
            ),
        ]
        for question, expected_answer, expected_unit, expected_strategy in samples:
            with self.subTest(expected_strategy=expected_strategy):
                result = solve_deterministic(question)
                self.assertIsNotNone(result)
                self.assertAlmostEqual(float(result.answer), float(expected_answer), places=3)
                self.assertEqual(result.unit, expected_unit)
                self.assertEqual(result.strategy, expected_strategy)

    def test_round3_vector_and_intent_regression_cases(self):
        samples = [
            (
                "Given two point charges located along the Ox axis: charge q1 = -9 x 10^-6 C is placed at the origin O, and charge q2 = 4 x 10^-6 C is located 20 cm from the origin. What is the coordinate on the Ox axis where the electric field strength is zero?",
                "60",
                "cm",
            ),
            (
                "A point charge q = +5 nC is in air. What is the electric field magnitude at a point 10 cm away? Use k = 9.0 x 10^9 N*m^2/C^2.",
                "4500",
                "N/C",
            ),
            (
                "In an oscillating LC circuit, when the electric field energy is 1/4 of the total energy, what percentage (%) of the maximum current is the instantaneous current (round the result to one decimal place)?",
                "86.6",
                "%",
            ),
            (
                "Three charges q1 = +2 μC, q2 = +2 μC, and q3 = -2 μC are placed at the three vertices of an equilateral triangle with a side length of 10 cm. Calculate the magnitude of the net electric force acting on q3.",
                "6.24",
                "N",
            ),
            (
                "Two charges are 20 cm apart and attract with force 0.09 N. If one charge is 1 uC, find the magnitude of the other charge. Use k = 9.0 x 10^9.",
                "0.4",
                "uC",
            ),
            (
                "Given a capacitor with C = 50 μF, what inductance L is required to achieve resonance at 200 Hz?",
                "12.67",
                "mH",
            ),
            (
                "Given L = 0.3 H, what capacitance C must be chosen for a capacitor to achieve resonance at a frequency of 120 Hz?",
                "5.86",
                "uF",
            ),
            (
                "Two point charges, q1 = 0.5 nC and q2 = -0.5 nC, are placed at points A and B, separated by 6 cm in air. What is the magnitude of the electric field intensity at point M, which lies on the perpendicular bisector of AB, at a distance ℓ = 4 cm from the midpoint of AB?",
                "2160",
                "V/m",
            ),
        ]
        for question, expected_answer, expected_unit in samples:
            with self.subTest(question=question):
                result = solve_deterministic(question)
                self.assertIsNotNone(result)
                final = f"{result.answer} {result.unit}".strip()
                comparison = compare_prediction(final, expected_answer, expected_unit, 1e-2, 1e-9)
                self.assertTrue(comparison[4], f"{final} != {expected_answer} {expected_unit}; strategy={result.strategy}")


if __name__ == "__main__":
    unittest.main()
