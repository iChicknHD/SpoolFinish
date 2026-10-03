import hashlib
import re
import tempfile
import unittest
from pathlib import Path

from spoolfinish.application import WorkflowController
from spoolfinish.material import mass_g
from spoolfinish.parser import analyze_text


PROJECT = Path(__file__).resolve().parents[2]
SIMULATIONS = (
    PROJECT / "tests" / "simulations" / "orcaslicer_2_4_2" / "plate_1.gcode",
    PROJECT / "tests" / "simulations" / "prusaslicer_2_9_6" / "plate_1.gcode",
)


class GuiRealSlicerSimulationTests(unittest.TestCase):
    def test_orca_and_prusa_workflows_through_application_controller(self):
        for source in SIMULATIONS:
            with self.subTest(slicer=source.parent.name), tempfile.TemporaryDirectory() as tmp:
                original = source.read_bytes()
                source_hash = hashlib.sha256(original).hexdigest()
                core_analysis = analyze_text(original.decode("utf-8"))
                reserve = 0.2
                remaining = mass_g(core_analysis.total_mm, "PLA") * 0.65 + reserve

                for firmware, command in (("Marlin", "M600"), ("Klipper", "PAUSE")):
                    controller = WorkflowController()
                    result = controller.analyze(source, str(remaining), str(reserve), "PLA", "1.75", firmware)
                    core_total = mass_g(core_analysis.total_mm, "PLA")
                    self.assertAlmostEqual(result.view.total_required_g, core_total)
                    self.assertAlmostEqual(result.view.usable_g, remaining - reserve)
                    self.assertTrue(result.view.change_required)
                    self.assertIsNotNone(result.view.change_before_layer)
                    self.assertEqual(result.view.change_before_layer, result.plan.change_before_layer + 1)

                    output = controller.create_patch(Path(tmp) / f"{source.parent.name}_{firmware}.gcode")
                    patched = output.read_bytes()
                    self.assertEqual(patched.count(f"\n{command}\n".encode()), 1)
                    reparsed = analyze_text(patched.decode("utf-8"))
                    self.assertEqual(len(reparsed.layers), len(core_analysis.layers))
                    self.assertAlmostEqual(reparsed.total_mm, core_analysis.total_mm, places=7)
                    self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), source_hash)


if __name__ == "__main__":
    unittest.main()
