import os, subprocess, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'simulations'/'orcaslicer_2_4_2'
SLICER=os.environ.get('SPOOLFINISH_ORCA_EXE')
@unittest.skipUnless(SLICER,'set SPOOLFINISH_ORCA_EXE and run the explicit slicer integration suite')
class OrcaRealSlicerIntegration(unittest.TestCase):
    def test_real_slicer_harness(self):
        result=subprocess.run([sys.executable,str(ROOT/'run_orca.py'),'--slicer',SLICER],capture_output=True,text=True,check=True,timeout=900)
        self.assertIn('OrcaSlicer',result.stdout)
        self.assertTrue((ROOT/'manifest.json').is_file())
        self.assertTrue((ROOT/'plate_1_marlin.gcode').is_file())
        self.assertTrue((ROOT/'plate_1_klipper.gcode').is_file())
if __name__=='__main__': unittest.main()
