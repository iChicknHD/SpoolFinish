import hashlib
import tempfile
import unittest
from pathlib import Path

from spoolfinish.application import ApplicationError, WorkflowController
from spoolfinish.material import mass_g
from spoolfinish.parser import analyze_text


SIMPLE_GCODE = """M83
G1 E1 F240
;LAYER_CHANGE
;Z:0.2
G1 E10 F240
;LAYER_CHANGE
;Z:0.4
G1 E10 F240
;LAYER_CHANGE
;Z:0.6
G1 E10 F240
"""


class ApplicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.source = self.directory / "print.gcode"
        self.source.write_text(SIMPLE_GCODE, encoding="utf-8")
        self.controller = WorkflowController()
        self.remaining = str(mass_g(16, "PLA"))
        self.reserve = str(mass_g(1, "PLA"))

    def analyze(self, **overrides):
        values = {
            "source": self.source,
            "remaining": self.remaining,
            "reserve": self.reserve,
            "material": "PLA",
            "diameter": "1.75",
            "firmware": "Marlin",
        }
        values.update(overrides)
        return self.controller.analyze(**values)

    def test_valid_analysis_maps_core_to_presentation_without_patching(self):
        result = self.analyze()
        self.assertTrue(result.view.change_required)
        self.assertAlmostEqual(result.view.total_required_g, result.plan.total_g)
        self.assertAlmostEqual(result.view.remaining_g, result.plan.available_g)
        self.assertAlmostEqual(result.view.reserve_g, result.plan.reserve_g)
        self.assertAlmostEqual(result.view.usable_g, result.plan.usable_g)
        self.assertEqual(result.view.change_before_layer, result.plan.change_before_layer + 1)
        self.assertAlmostEqual(result.view.change_z_mm, result.plan.change_z)
        self.assertFalse((self.directory / "print_spoolfinish.gcode").exists())

    def test_invalid_numeric_inputs(self):
        for field, value in (("remaining", ""), ("remaining", "-1"), ("reserve", "many"),
                             ("diameter", "0"), ("diameter", "NaN")):
            with self.subTest(field=field, value=value), self.assertRaises(ApplicationError):
                self.analyze(**{field: value})

    def test_missing_file_and_unsupported_extension(self):
        with self.assertRaisesRegex(ApplicationError, "file not found"):
            self.analyze(source=self.directory / "missing.gcode")
        text_file = self.directory / "print.txt"
        text_file.write_text(SIMPLE_GCODE, encoding="utf-8")
        with self.assertRaisesRegex(ApplicationError, "text G-code"):
            self.analyze(source=text_file)

    def test_reserve_cannot_exceed_remaining(self):
        with self.assertRaisesRegex(ApplicationError, "cannot exceed"):
            self.analyze(remaining="1", reserve="2")

    def test_change_required_no_and_patch_disabled_in_controller(self):
        total = mass_g(analyze_text(SIMPLE_GCODE).total_mm, "PLA")
        result = self.analyze(remaining=str(total + 1), reserve="0")
        self.assertFalse(result.view.change_required)
        with self.assertRaisesRegex(ApplicationError, "not necessary"):
            self.controller.create_patch()
        self.assertFalse((self.directory / "print_spoolfinish.gcode").exists())

    def test_unsupported_core_result_clears_prior_result_and_cannot_patch(self):
        self.analyze()
        self.source.write_text("M83\nM221 S100\n;LAYER_CHANGE\nG1 E1\n", encoding="utf-8")
        with self.assertRaisesRegex(ApplicationError, "Unsupported extrusion semantics"):
            self.analyze()
        self.assertIsNone(self.controller.current_result)
        with self.assertRaisesRegex(ApplicationError, "Analyze a valid"):
            self.controller.create_patch()

    def test_missing_layer_markers_are_explained(self):
        self.source.write_text("M83\nG1 E1\n", encoding="utf-8")
        with self.assertRaisesRegex(ApplicationError, "No supported deterministic layer markers"):
            self.analyze()

    def test_marlin_and_klipper_patch_creation_collision_and_source_preservation(self):
        source_hash = hashlib.sha256(self.source.read_bytes()).hexdigest()
        for firmware, command in (("Marlin", "M600"), ("Klipper", "PAUSE")):
            with self.subTest(firmware=firmware):
                self.analyze(firmware=firmware)
                output = self.controller.create_patch(self.directory / f"{firmware}.gcode")
                data = output.read_bytes()
                self.assertEqual(data.decode("utf-8").splitlines().count(command), 1)
                with self.assertRaisesRegex(ApplicationError, "already exists"):
                    self.controller.create_patch(output)
                self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(), source_hash)


if __name__ == "__main__":
    unittest.main()
