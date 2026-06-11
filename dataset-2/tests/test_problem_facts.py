import unittest

from app.modules.problem_facts import analyze_problem


class ProblemFactsTests(unittest.TestCase):
    def test_chained_distances_detect_midpoint(self):
        facts = analyze_problem(
            "Two charges are separated by 10 cm. Point M has MA = MB = 5 cm."
        )

        self.assertIn("M", facts.midpoint_points)
        self.assertTrue(facts.has_collinear)
        self.assertAlmostEqual(facts.distances_m["MA"], 0.05)
        self.assertAlmostEqual(facts.distances_m["AB"], 0.10)

    def test_collinear_relation_detects_external_point(self):
        facts = analyze_problem(
            "A and B are 10 cm apart. Given NA = 5 cm and NB = 15 cm."
        )

        joined = "\n".join(facts.collinear_facts)
        self.assertIn("NA + AB = NB", joined)
        self.assertIn("A lies between N and B", joined)

    def test_symbolic_and_square_mixed_sign(self):
        facts = analyze_problem(
            "Four charges of magnitude q (C) are at square ABCD with side length a (m). "
            "Positive charges are at A and D, negative charges at B and C. Determine the field at the intersection of diagonals."
        )

        self.assertTrue(facts.asks_symbolic)
        self.assertTrue(facts.square_center)
        self.assertTrue(facts.square_mixed_sign)

    def test_zero_field_region_from_signs(self):
        opposite = analyze_problem(
            "q1 = -9 x 10^-6 C and q2 = 4 x 10^-6 C are separated by 20 cm. Find where the electric field is zero."
        )
        same = analyze_problem(
            "q1 = -9 x 10^-6 C and q2 = -4 x 10^-6 C are separated by 20 cm. Find where the electric field is zero."
        )

        self.assertEqual(opposite.zero_field_region, "outside")
        self.assertEqual(same.zero_field_region, "between")


if __name__ == "__main__":
    unittest.main()
