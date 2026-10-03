import runpy
import tempfile
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
RUNNER = PROJECT / "tests" / "simulations" / "prusaslicer_2_9_6" / "run_prusa.py"
portable_manifest_argument = runpy.run_path(str(RUNNER), run_name="manifest_privacy_test")[
    "portable_manifest_argument"
]


class PrusaManifestPrivacyTests(unittest.TestCase):
    def test_project_paths_are_stored_relative_to_repository(self):
        source = PROJECT / "tests" / "simulations" / "prusaslicer_2_9_6" / "cube_20mm.stl"

        self.assertEqual(
            portable_manifest_argument(str(source)),
            "tests/simulations/prusaslicer_2_9_6/cube_20mm.stl",
        )

    def test_external_tool_paths_are_stored_by_filename_only(self):
        executable = Path(tempfile.gettempdir()) / "PrusaSlicer" / "prusa-slicer-console.exe"

        self.assertEqual(
            portable_manifest_argument(str(executable)),
            "prusa-slicer-console.exe",
        )

    def test_relative_arguments_are_preserved(self):
        self.assertEqual(portable_manifest_argument("--start-gcode"), "--start-gcode")


if __name__ == "__main__":
    unittest.main()
