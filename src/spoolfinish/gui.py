"""Compact local Tkinter user interface for the SpoolFinish core workflow."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, ttk

from .application import (
    ApplicationError,
    FIRMWARES,
    MATERIALS,
    WorkflowController,
    format_remainder_g,
)
from .material import DEFAULT_DIAMETER_MM


class SpoolFinishWindow:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.controller = WorkflowController()
        root.title("SpoolFinish")
        root.geometry("590x490")
        root.minsize(560, 460)

        self.path = tk.StringVar()
        self.remaining = tk.StringVar()
        self.reserve = tk.StringVar(value="0")
        self.material = tk.StringVar(value="PLA")
        self.diameter = tk.StringVar(value=str(DEFAULT_DIAMETER_MM))
        self.firmware = tk.StringVar(value="Marlin")
        self.status = tk.StringVar()
        self.created = tk.StringVar()
        self._result_labels: dict[str, ttk.Label] = {}

        body = ttk.Frame(root, padding=16)
        body.pack(fill="both", expand=True)
        body.columnconfigure(1, weight=1)

        ttk.Label(body, text="G-code file").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(body, textvariable=self.path, state="readonly").grid(row=0, column=1, sticky="ew", padx=8, pady=5)
        ttk.Button(body, text="Browse...", command=self._browse).grid(row=0, column=2, sticky="e", pady=5)

        ttk.Label(body, text="Remaining filament [g]").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(body, textvariable=self.remaining, width=16).grid(row=1, column=1, sticky="w", padx=8, pady=5)
        ttk.Label(body, text="Safety reserve [g]").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(body, textvariable=self.reserve, width=16).grid(row=2, column=1, sticky="w", padx=8, pady=5)

        ttk.Label(body, text="Material").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Combobox(body, textvariable=self.material, values=MATERIALS, state="readonly", width=14).grid(
            row=3, column=1, sticky="w", padx=8, pady=5
        )
        ttk.Label(body, text="Diameter [mm]").grid(row=4, column=0, sticky="w", pady=5)
        ttk.Entry(body, textvariable=self.diameter, width=16).grid(row=4, column=1, sticky="w", padx=8, pady=5)
        ttk.Label(body, text="Firmware").grid(row=5, column=0, sticky="w", pady=5)
        ttk.Combobox(body, textvariable=self.firmware, values=FIRMWARES, state="readonly", width=14).grid(
            row=5, column=1, sticky="w", padx=8, pady=5
        )

        self.analyze_button = ttk.Button(body, text="Analyze", command=self._analyze)
        self.analyze_button.grid(row=6, column=0, sticky="w", pady=(10, 8))
        ttk.Label(body, textvariable=self.status, foreground="#9b1c1c", wraplength=540).grid(
            row=7, column=0, columnspan=3, sticky="w", pady=4
        )

        results = ttk.LabelFrame(body, text="Analysis result", padding=10)
        results.grid(row=8, column=0, columnspan=3, sticky="ew", pady=(8, 10))
        results.columnconfigure(1, weight=1)
        for index, (key, label) in enumerate((
            ("total", "Total required"),
            ("remaining", "Spool remaining"),
            ("reserve", "Safety reserve"),
            ("usable", "Usable"),
            ("change", "Change required"),
            ("layer", "Change before layer"),
            ("z", "Z height"),
            ("consumed", "Consumed before change"),
            ("remainder", "Expected remainder"),
        )):
            ttk.Label(results, text=label).grid(row=index, column=0, sticky="w", padx=(0, 18), pady=2)
            value = ttk.Label(results, text="")
            value.grid(row=index, column=1, sticky="w", pady=2)
            self._result_labels[key] = value

        self.patch_button = ttk.Button(body, text="Create patched G-code", command=self._create_patch, state="disabled")
        self.patch_button.grid(row=9, column=0, sticky="w", pady=4)
        ttk.Label(body, textvariable=self.created, wraplength=540).grid(row=10, column=0, columnspan=3, sticky="w", pady=3)

        for variable in (self.path, self.remaining, self.reserve, self.material, self.diameter, self.firmware):
            variable.trace_add("write", self._inputs_changed)

    def _inputs_changed(self, *_: object) -> None:
        self.controller.invalidate()
        self.patch_button.configure(state="disabled")
        self.status.set("")
        self.created.set("")
        for label in self._result_labels.values():
            label.configure(text="")

    def _browse(self) -> None:
        filename = filedialog.askopenfilename(
            title="Select G-code",
            filetypes=(("Text G-code", "*.gcode *.gco *.gc"), ("All files", "*.*")),
        )
        if filename:
            self.path.set(filename)

    def _analyze(self) -> None:
        try:
            result = self.controller.analyze(
                self.path.get(), self.remaining.get(), self.reserve.get(), self.material.get(),
                self.diameter.get(), self.firmware.get(),
            )
        except ApplicationError as exc:
            self._inputs_changed()
            self.status.set(str(exc))
            return

        view = result.view
        values = {
            "total": f"{view.total_required_g:.2f} g",
            "remaining": f"{view.remaining_g:.2f} g",
            "reserve": f"{view.reserve_g:.2f} g",
            "usable": f"{view.usable_g:.2f} g",
            "change": "YES" if view.change_required else "NO",
            "layer": (str(view.change_before_layer) if view.change_required else ""),
            "z": (f"{view.change_z_mm:.2f} mm" if view.change_z_mm is not None else "unknown"),
            "consumed": (f"{view.consumed_before_change_g:.2f} g" if view.change_required else ""),
            "remainder": (format_remainder_g(view.expected_remainder_g) if view.change_required else ""),
        }
        for key, text in values.items():
            self._result_labels[key].configure(text=text)
        self.patch_button.configure(state="normal" if view.change_required else "disabled")
        self.status.set("")
        self.created.set("")

    def _create_patch(self) -> None:
        try:
            output = self.controller.create_patch()
        except ApplicationError as exc:
            self.status.set(str(exc))
            return
        self.status.set("")
        self.created.set(f"Created:\n{output}")


def main() -> None:
    root = tk.Tk()
    SpoolFinishWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
