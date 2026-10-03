"""Thin GUI-facing workflow layer over SpoolFinish Core."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from .models import Analysis
from .parser import GcodeError, analyze_text
from .patcher import default_output, patch
from .planner import Plan, PlanError, plan_change

SUPPORTED_EXTENSIONS = {".gcode", ".gco", ".gc"}
MATERIALS = ("PLA", "PETG", "ABS", "ASA")
FIRMWARES = ("Marlin", "Klipper")


class ApplicationError(ValueError):
    """A safe, user-facing workflow error without implementation details."""


@dataclass(frozen=True)
class ResultView:
    total_required_g: float
    remaining_g: float
    reserve_g: float
    usable_g: float
    change_required: bool
    # User-facing layer number (one-based); the Core Plan remains zero-based.
    change_before_layer: int | None
    change_z_mm: float | None
    consumed_before_change_g: float
    expected_remainder_g: float


def display_layer_number(core_index: int | None) -> int | None:
    """Convert a zero-based Core layer index to the user-facing layer number."""
    return None if core_index is None else core_index + 1


def format_remainder_g(value: float) -> str:
    """Format expected remainder without hiding a small positive amount."""
    if value == 0:
        return "0.00 g"
    if 0 < value < 0.01:
        return "< 0.01 g"
    return f"{value:.2f} g"


@dataclass(frozen=True)
class AnalysisResult:
    source: Path
    material: str
    diameter_mm: float
    firmware: str
    analysis: Analysis
    plan: Plan
    view: ResultView


def _number(value: str, label: str, *, allow_zero: bool = True) -> float:
    candidate = value.strip().replace(",", ".")
    if not candidate:
        raise ApplicationError(f"Enter {label.lower()}.")
    try:
        parsed = float(candidate)
    except ValueError as exc:
        raise ApplicationError(f"{label} must be a number.") from exc
    if not math.isfinite(parsed):
        raise ApplicationError(f"{label} must be a finite number.")
    if parsed < 0 or (not allow_zero and parsed == 0):
        qualifier = "greater than zero" if not allow_zero else "zero or greater"
        raise ApplicationError(f"{label} must be {qualifier}.")
    return parsed


def _core_message(error: GcodeError) -> str:
    message = str(error)
    if "no ;LAYER_CHANGE" in message:
        return "No supported deterministic layer markers found."
    if "UNSUPPORTED / CANNOT SAFELY PATCH" in message:
        return "Unsupported extrusion semantics detected. Cannot safely analyze this G-code."
    return "Cannot safely analyze this G-code."


class WorkflowController:
    """Coordinates analyze and patch actions; it contains no G-code logic."""

    def __init__(self) -> None:
        self.current_result: AnalysisResult | None = None

    def invalidate(self) -> None:
        self.current_result = None

    def analyze(
        self,
        source: str | Path,
        remaining: str,
        reserve: str,
        material: str,
        diameter: str,
        firmware: str,
    ) -> AnalysisResult:
        self.invalidate()
        path_text = str(source).strip()
        if not path_text:
            raise ApplicationError("Select a G-code file.")

        source_path = Path(path_text).expanduser()
        if source_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise ApplicationError("Choose a text G-code file (.gcode, .gco or .gc).")
        if not source_path.is_file():
            raise ApplicationError("G-code file not found.")
        source_path = source_path.resolve()

        remaining_g = _number(remaining, "Remaining filament")
        reserve_g = _number(reserve, "Safety reserve")
        diameter_mm = _number(diameter, "Diameter", allow_zero=False)
        material = material.upper().strip()
        firmware = firmware.strip().lower()
        if material not in MATERIALS:
            raise ApplicationError("Choose PLA, PETG, ABS or ASA.")
        if firmware not in {item.lower() for item in FIRMWARES}:
            raise ApplicationError("Choose Marlin or Klipper.")
        if reserve_g > remaining_g:
            raise ApplicationError("Safety reserve cannot exceed remaining filament.")

        try:
            text = source_path.read_text(encoding="utf-8-sig")
            analysis = analyze_text(text)
            plan = plan_change(analysis, remaining_g, reserve_g, material, diameter_mm)
        except GcodeError as exc:
            raise ApplicationError(_core_message(exc)) from exc
        except PlanError as exc:
            raise ApplicationError(str(exc)) from exc
        except UnicodeError as exc:
            raise ApplicationError("Cannot read this file as text G-code.") from exc
        except OSError as exc:
            raise ApplicationError(f"Cannot read G-code file: {exc.strerror or 'access error'}.") from exc
        except ValueError as exc:
            raise ApplicationError("Cannot safely analyze this G-code.") from exc

        view = ResultView(
            total_required_g=plan.total_g,
            remaining_g=plan.available_g,
            reserve_g=plan.reserve_g,
            usable_g=plan.usable_g,
            change_required=plan.change_required,
            change_before_layer=display_layer_number(plan.change_before_layer),
            change_z_mm=plan.change_z,
            consumed_before_change_g=plan.consumed_before_g,
            expected_remainder_g=plan.remainder_g,
        )
        result = AnalysisResult(source_path, material, diameter_mm, firmware, analysis, plan, view)
        self.current_result = result
        return result

    def create_patch(self, output: str | Path | None = None) -> Path:
        result = self.current_result
        if result is None:
            raise ApplicationError("Analyze a valid G-code file before creating a patched copy.")
        if not result.plan.change_required:
            raise ApplicationError("No change is required; a patched copy is not necessary.")
        destination = Path(output) if output is not None else default_output(result.source)
        try:
            return patch(result.source, destination, result.plan, result.firmware)
        except GcodeError as exc:
            message = str(exc)
            if "output already exists" in message:
                raise ApplicationError("Output already exists. Rename or move it before retrying.") from exc
            if "output path must differ" in message:
                raise ApplicationError("Output must be a separate file from the source G-code.") from exc
            raise ApplicationError("Cannot create patched G-code safely.") from exc
        except OSError as exc:
            raise ApplicationError(f"Cannot create output file: {exc.strerror or 'file access error'}.") from exc
