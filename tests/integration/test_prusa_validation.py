import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "simulations" / "prusaslicer_2_9_6"
SLICER = os.environ.get("SPOOLFINISH_PRUSA_EXE")


@unittest.skipUnless(SLICER, "set SPOOLFINISH_PRUSA_EXE and run the explicit PrusaSlicer integration suite")
class PrusaRealSlicerIntegration(unittest.TestCase):
    def test_real_slicer_harness(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "run_prusa.py"), "--slicer", SLICER],
            capture_output=True,
            text=True,
            check=True,
            timeout=900,
        )
        self.assertIn('"slicer_version": "2.9.6"', result.stdout)
        self.assertTrue((ROOT / "manifest.json").is_file())
        self.assertTrue((ROOT / "plate_1_marlin.gcode").is_file())
        self.assertTrue((ROOT / "plate_1_klipper.gcode").is_file())


if __name__ == "__main__":
    unittest.main()
