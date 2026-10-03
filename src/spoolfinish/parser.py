import re
from .models import Analysis, Layer, ExtrusionMode

_NUM = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)"
_WORD = re.compile(rf"([A-Za-z])\s*({_NUM})")
_EWORD = re.compile(rf"(?:^|\s)E\s*({_NUM})(?=\s|$)", re.I)
_LAYER = re.compile(r"^\s*;LAYER_CHANGE\s*$", re.I)
_Z = re.compile(rf"^\s*;Z:({_NUM})\s*$", re.I)
_UNSUPPORTED = {"G2", "G3", "G5", "G10", "G11", "M200", "M207", "M208", "M221"}
# E parameters on these motion-limit commands configure acceleration/speed/jerk;
# they do not represent filament motion. Flow scaling (M221) remains unsupported.
_NON_ACCOUNTING_E = {"M201", "M203", "M204", "M205"}

class GcodeError(ValueError):
    pass

def analyze_text(text: str) -> Analysis:
    lines = tuple(text.splitlines(keepends=True))
    mode = ExtrusionMode.UNKNOWN
    logical_e = debt = consumed = 0.0
    cumulative = []
    for i, raw in enumerate(lines):
        stripped = raw.split(';', 1)[0].strip()
        words = _WORD.findall(stripped)
        command = next((f"{a.upper()}{v}" for a, v in words if a.upper() in "GMT"), None)
        code = None
        if command:
            cm = re.match(r"([GMT])([+-]?\d+)", command)
            if cm:
                code = f"{cm.group(1)}{int(cm.group(2))}"
        if code:
            if code in _UNSUPPORTED:
                raise GcodeError(f"UNSUPPORTED / CANNOT SAFELY PATCH: {code} at line {i+1}")
            if code.startswith("T") and code != "T0":
                raise GcodeError(f"UNSUPPORTED / CANNOT SAFELY PATCH: multi-tool command {code} at line {i+1}")
            if code in ("M82", "M83"):
                mode = ExtrusionMode.ABSOLUTE if code == "M82" else ExtrusionMode.RELATIVE
            elif code == "G92":
                em = _EWORD.search(stripped)
                has_e = re.search(r"(?:^|\s)E", stripped, re.I)
                if has_e and not em:
                    raise GcodeError(f"UNSUPPORTED / CANNOT SAFELY PATCH: malformed E word at line {i+1}")
                if em:
                    logical_e = float(em.group(1))
            elif code in ("G0", "G1"):
                em = _EWORD.search(stripped)
                has_e = re.search(r"(?:^|\s)E", stripped, re.I)
                if has_e and not em:
                    raise GcodeError(f"UNSUPPORTED / CANNOT SAFELY PATCH: malformed E word at line {i+1}")
                if em:
                    e = float(em.group(1))
                    if mode is ExtrusionMode.UNKNOWN:
                        raise GcodeError(f"UNSUPPORTED / CANNOT SAFELY PATCH: extrusion before M82/M83 at line {i+1}")
                    if mode is ExtrusionMode.ABSOLUTE:
                        delta = e - logical_e
                        logical_e = e
                    else:
                        delta = e
                        logical_e += e
                    if delta < 0:
                        debt += -delta
                    elif delta > 0:
                        restored = min(delta, debt)
                        debt -= restored
                        consumed += delta - restored
            elif re.search(r"(?:^|\s)E", stripped, re.I) and code not in _NON_ACCOUNTING_E:
                raise GcodeError(f"UNSUPPORTED / CANNOT SAFELY PATCH: E on {code} at line {i+1}")
        cumulative.append(consumed)

    markers = [i for i, line in enumerate(lines) if _LAYER.match(line.rstrip("\r\n"))]
    if not markers:
        raise GcodeError("UNSUPPORTED / CANNOT SAFELY PATCH: no ;LAYER_CHANGE boundaries")
    startup = cumulative[markers[0] - 1] if markers[0] else 0.0
    layers = []
    previous = startup
    for idx, marker in enumerate(markers):
        z = None
        for meta in lines[marker + 1:min(marker + 5, len(lines))]:
            zm = _Z.match(meta.rstrip("\r\n"))
            if zm:
                z = float(zm.group(1))
                break
            if _LAYER.match(meta.rstrip("\r\n")):
                break
        end = markers[idx + 1] if idx + 1 < len(markers) else len(lines)
        total = cumulative[end - 1] if end else 0.0
        layers.append(Layer(idx, marker, z, total - previous, total))
        previous = total
    return Analysis(lines, startup, tuple(layers), consumed)
