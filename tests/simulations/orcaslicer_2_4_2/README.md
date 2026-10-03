# OrcaSlicer real-engine simulation

Generated locally with the official OrcaSlicer 2.4.2 Windows x64 portable release and its bundled Prusa MK3S 0.4 mm profiles. `cube_20mm.stl` is a local closed cube mesh; no printer is connected or required.

The checked-in `machine.json`, `process.json`, and `filament.json` are resolved copies of the bundled official presets. The machine start/end G-code was adjusted only to remove M221 flow scaling and end-of-print effects, and the process disables prime-tower generation. The resulting engine output has a single extruder, PLA at 1.75 mm, 0.20 mm layers, 0.2 mm Z-hop, explicit M83, and `;LAYER_CHANGE` / `;Z:` annotations. The generated file includes Z-hop motion; layer accounting follows only the 100 explicit layer markers, not Z moves.

Reproduce with Python 3.12 and the extracted official portable release:

```powershell
python tests/simulations/orcaslicer_2_4_2/run_orca.py --slicer C:\path\to\orca-slicer.exe
```

`plate_1.gcode` is the engine output. `cube_sliced.3mf` contains Orca's independent `Metadata/slice_info.config` oracle (`used_m`, `used_g`). The runner compares rounded `used_m` with a 5.01 mm tolerance (metadata rounded to 0.01 m) and `used_g` with a 0.0051 g tolerance (two decimal places). It then generates separate Marlin and Klipper patched copies and checks exact preservation outside the injected block. `manifest.json` records versions, hashes, comparisons, layer totals, planner edges, and static patch checks.

Firmware checks are structural only: Marlin M600 needs compatible firmware support such as `ADVANCED_PAUSE_FEATURE`; Klipper PAUSE needs `pause_resume`. No physical execution is claimed.
