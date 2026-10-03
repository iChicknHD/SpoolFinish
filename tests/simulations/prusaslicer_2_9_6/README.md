# PrusaSlicer real-engine simulation

This fixture uses the official PrusaSlicer 2.9.6 Windows ZIP release and its `prusa-slicer-console.exe`. The ZIP SHA-256 is recorded in `manifest.json`. No installer, printer connection, MMU, or physical device is used.

The model is the same locally generated closed 20 mm cube as the OrcaSlicer 2.4.2 simulation. Slicing uses the official CLI defaults with explicit deterministic overrides: single-extruder Marlin-flavor FDM, PLA, 1.75 mm filament, 0.4 mm nozzle, 0.20 mm layers, relative E, 0.2 mm retraction lift, no wipe tower, and a 3 mm startup prime. There is no named printer profile; the CLI uses its built-in generic defaults. The prime is part of the generated start G-code, not a post-generation edit.

The runner stores the real engine output as `plate_1.gcode`, compares its `; filament used [mm]` metadata with SpoolFinish's higher precision total, exercises safe-change boundaries, and writes separately patched Marlin and Klipper copies. PrusaSlicer's length metadata is printed to 0.01 mm, so the comparison tolerance is 0.0051 mm (half a rounding unit plus 0.0001 mm numeric margin). The `g` field is 0.00 with the CLI default material profile, so it is not used as an oracle.

Reproduce after extracting the official ZIP:

```powershell
python tests/simulations/prusaslicer_2_9_6/run_prusa.py --slicer C:\path\to\PrusaSlicer-2.9.6\prusa-slicer-console.exe
```

`manifest.json` records the exact arguments, metadata comparison, layer and Z-hop counts, planner edges, source hash, and structural patch checks. This establishes static G-code behavior only; firmware runtime is not exercised.
