import hashlib, math, tempfile, unittest
from pathlib import Path
from spoolfinish.parser import analyze_text, GcodeError
from spoolfinish.material import mass_g
from spoolfinish.planner import plan_change, PlanError
from spoolfinish.patcher import patch

class CoreTests(unittest.TestCase):
 def test_modes_and_g92(self):
  a=analyze_text("M82\nG1 E10\nG92 E0\nG1 E2\n") if False else None
  with self.assertRaises(GcodeError): analyze_text("G1 E2\n;LAYER_CHANGE\n")
  a=analyze_text("M82\nG1 E10\nG92 E0\nG1 E2\n;LAYER_CHANGE\nG1 E3\n")
  self.assertAlmostEqual(a.total_mm,13)
  b=analyze_text("M83\nG1 E10\nG92 E50\nG1 E2\n;LAYER_CHANGE\n")
  self.assertAlmostEqual(b.total_mm,12)
 def test_retract_debt(self):
  a=analyze_text("M83\nG1 E-0.8\nG1 E-0.4\nG1 E1.0\nG1 E0.5\n;LAYER_CHANGE\n")
  self.assertAlmostEqual(a.total_mm,.3)
 def test_formats_comments_and_non_extrusion(self):
  a=analyze_text("; header\n\nM83 ; relative\nG1 X1 Y2 ; no E\nG1 E+2\nG1 E.5\nG1 E-1\nG1 E1 ; restore\n;LAYER_CHANGE\nG1 E3\n")
  self.assertAlmostEqual(a.total_mm,5.5)
 def test_layers_z_hop_and_startup(self):
  a=analyze_text("M83\nG1 E1\n;LAYER_CHANGE\n;Z:0.2\nG1 Z0.4\nG1 Z0.2\nG1 E2\n;LAYER_CHANGE\n;Z:0.4\nG1 E3\n")
  self.assertEqual(len(a.layers),2); self.assertAlmostEqual(a.startup_mm,1); self.assertAlmostEqual(a.layers[0].consumed_mm,2); self.assertAlmostEqual(a.total_mm,6)
 def test_errors_fail_closed(self):
  for s in ("M200 D1.75\n;LAYER_CHANGE\n","M83\nG2 X1 E2\n;LAYER_CHANGE\n","M83\nT1\n;LAYER_CHANGE\n","M83\nG1 Ebad\n;LAYER_CHANGE\n","M83\nG92 Ebad\n;LAYER_CHANGE\n","M83\nG1 E1e-3\n;LAYER_CHANGE\n"):
   with self.assertRaises(GcodeError): analyze_text(s)
 def test_planner_boundaries(self):
  a=analyze_text("M83\n;LAYER_CHANGE\nG1 E10\n;LAYER_CHANGE\nG1 E10\n;LAYER_CHANGE\nG1 E10\n")
  unit=mass_g(1,"PLA")
  p=plan_change(a,15*unit,0,"PLA",1.75); self.assertTrue(p.change_required); self.assertEqual(p.change_before_layer,1)
  exact=plan_change(a,10*unit,0,"PLA",1.75); self.assertEqual(exact.change_before_layer,1)
  fits=plan_change(a,40*unit,0,"PLA",1.75); self.assertFalse(fits.change_required)
  with self.assertRaises(PlanError): plan_change(a,1,2,"PLA",1.75)
 def test_patch_and_nonoverwrite(self):
  a=analyze_text("M83\n;LAYER_CHANGE\nG1 E10\n;LAYER_CHANGE\nG1 E10\n")
  plan=plan_change(a,mass_g(10,"PLA")*1.5,0,"PLA",1.75)
  with tempfile.TemporaryDirectory() as d:
   src=Path(d)/"x.gcode"; out=Path(d)/"out.gcode"; src.write_bytes(b"M83\r\n;LAYER_CHANGE\r\nG1 E10\r\n;LAYER_CHANGE\r\nG1 E10\r\n")
   before=hashlib.sha256(src.read_bytes()).digest(); patch(src,out,plan,"klipper")
   self.assertEqual(hashlib.sha256(src.read_bytes()).digest(),before); data=out.read_bytes(); self.assertIn(b"PAUSE",data); self.assertLess(data.index(b"PAUSE"),data.index(b";LAYER_CHANGE",data.index(b";LAYER_CHANGE")+1))
   with self.assertRaises(GcodeError): patch(src,out,plan,"marlin")
 def test_reasonably_large_input(self):
  s="M83\n"+"G1 E0.01\n"*10000+";LAYER_CHANGE\n"+"G1 E0.01\n"*10000
  a=analyze_text(s)
  self.assertEqual(len(a.layers),1); self.assertAlmostEqual(a.total_mm,200)
 def test_malformed_irrelevant_line(self):
  a=analyze_text("not a command ???\nM83\n;LAYER_CHANGE\nG1 E2\n")
  self.assertAlmostEqual(a.total_mm,2)
 def test_density(self):
  self.assertAlmostEqual(mass_g(1000,"PLA"),math.pi*(1.75/2)**2*1.24,places=10)
  self.assertGreater(mass_g(100,"PLA",1.75,1.30),mass_g(100,"PLA"))
 def test_non_consumption_e_axis_parameter(self):
  a=analyze_text("M83\nM201 E5000\n;LAYER_CHANGE\nG1 E2\n")
  self.assertAlmostEqual(a.total_mm,2)

if __name__=="__main__": unittest.main()
