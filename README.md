# SpoolFinish Core Proof

A bounded, single-extruder G-code material accounting proof. Supports explicit M82/M83 semantics, G0/G1 E moves, G92 E, slicer `;LAYER_CHANGE` markers, and Marlin M600 or Klipper PAUSE insertion. Unsupported material-affecting semantics fail closed.

Material defaults in `material.py` (g/cm^3): PLA 1.24, PETG 1.27, ABS 1.04, ASA 1.07. They are engineering defaults and should be validated against the selected filament.

`SAFE_CHANGE_LAYER` is the zero-based next layer before which the pause is inserted. Startup use counts against the available material. If print fits, no output is written.

Run: `python -m spoolfinish.cli analyze print.gcode --remaining 83 --reserve 5 --material PLA --firmware marlin`

Use `--diameter` to override filament diameter (default 1.75 mm) and `--density` to override the selected material's density in g/cm^3.

## Desktop MVP

Launch with `python -m spoolfinish.gui` (or `spoolfinish-gui` after installing the package).

1. Select a G-code file.
2. Enter remaining filament and safety reserve in grams.
3. Choose material, diameter, and firmware.
4. Select **Analyze**.
5. If a change is needed, select **Create patched G-code**.

The source G-code is never overwritten; an existing output is never silently replaced. Marlin `M600` requires compatible firmware support such as `ADVANCED_PAUSE_FEATURE`. Klipper `PAUSE` requires the `pause_resume` module. SpoolFinish performs static G-code planning; physical printer execution is not guaranteed or tested.

## Windows portable

1. Extract `SpoolFinish-portable-windows-x64.zip`.
2. Run `SpoolFinish.exe` from the extracted `SpoolFinish` folder.
3. Browse for a `.gcode` file.
4. Enter remaining filament and safety reserve.
5. Select **Analyze**.
6. Select **Create patched G-code** if a change is required.

The source G-code is never overwritten. Windows may show a reputation warning because this MVP executable is unsigned. No installer is required.

