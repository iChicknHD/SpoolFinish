import unittest

from spoolfinish.application import display_layer_number, format_remainder_g


class PresentationTests(unittest.TestCase):
    def test_core_layer_indices_are_presented_one_based(self):
        self.assertEqual(display_layer_number(0), 1)
        self.assertEqual(display_layer_number(67), 68)
        self.assertIsNone(display_layer_number(None))

    def test_expected_remainder_preserves_near_zero_information(self):
        self.assertEqual(format_remainder_g(0), "0.00 g")
        self.assertEqual(format_remainder_g(0.004), "< 0.01 g")
        self.assertEqual(format_remainder_g(0.012), "0.01 g")


if __name__ == "__main__":
    unittest.main()
