from pathlib import Path
from .parser import GcodeError
from .planner import Plan
def default_output(source:Path)->Path: return source.with_name(source.stem+"_spoolfinish.gcode")
def patch(source:Path, output:Path, plan:Plan, firmware:str)->Path:
    source=source.resolve(); output=output.resolve()
    if source==output: raise GcodeError("output path must differ from input")
    if output.exists(): raise GcodeError(f"output already exists: {output}")
    if not plan.change_required: raise GcodeError("no change required; output not created")
    if plan.boundary_line is None: raise GcodeError("no following layer boundary available for required change")
    cmd={"marlin":"M600","klipper":"PAUSE"}.get(firmware.lower())
    if cmd is None: raise GcodeError("firmware must be marlin or klipper")
    data=source.read_bytes(); lines=data.splitlines(keepends=True)
    i=plan.boundary_line; newline=b"\r\n" if b"\r\n" in data else b"\n"
    injected=f"; SPOOLFINISH_CHANGE_BEGIN\n{cmd}\n; SPOOLFINISH_CHANGE_END\n".encode()
    # Match original line ending convention and insert directly before ;LAYER_CHANGE.
    injected=injected.replace(b"\n",newline)
    with output.open("xb") as stream:
        stream.write(b"".join(lines[:i]) + injected + b"".join(lines[i:]))
    return output
