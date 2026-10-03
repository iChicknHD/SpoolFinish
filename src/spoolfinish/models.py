from dataclasses import dataclass
from enum import Enum

class ExtrusionMode(str, Enum):
    UNKNOWN = "UNKNOWN"
    ABSOLUTE = "ABSOLUTE"
    RELATIVE = "RELATIVE"

@dataclass(frozen=True)
class Layer:
    index: int
    boundary_line: int
    z_mm: float | None
    consumed_mm: float
    cumulative_mm: float

@dataclass(frozen=True)
class Analysis:
    lines: tuple[str, ...]
    startup_mm: float
    layers: tuple[Layer, ...]
    total_mm: float
