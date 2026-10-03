from dataclasses import dataclass
from .models import Analysis, Layer
from .material import mass_g

class PlanError(ValueError): pass
@dataclass(frozen=True)
class Plan:
    change_required: bool
    last_completed_layer: int|None
    change_before_layer: int|None
    boundary_line: int|None
    change_z: float|None
    total_g: float
    available_g: float
    reserve_g: float
    usable_g: float
    consumed_before_g: float
    remainder_g: float

def plan_change(a:Analysis, remaining_g:float,reserve_g:float,material:str,diameter:float,density_g_cm3:float|None=None)->Plan:
    if remaining_g<0 or reserve_g<0: raise PlanError("remaining and reserve must be nonnegative")
    if reserve_g>remaining_g: raise PlanError("reserve exceeds remaining material")
    usable=remaining_g-reserve_g; total=mass_g(a.total_mm,material,diameter,density_g_cm3)
    if total<=usable: return Plan(False,None,None,None,None,total,remaining_g,reserve_g,usable,total,usable-total)
    startup=mass_g(a.startup_mm,material,diameter,density_g_cm3)
    if startup>usable: raise PlanError("startup consumption exceeds usable material; no safe layer boundary")
    selected=None
    for layer in a.layers:
        if mass_g(layer.cumulative_mm,material,diameter,density_g_cm3)<=usable: selected=layer
        else: break
    # selected layer completion means insertion at next layer start; if none, insert before layer 0.
    next_index=0 if selected is None else selected.index+1
    boundary=a.layers[next_index].boundary_line if next_index<len(a.layers) else None
    z=a.layers[next_index].z_mm if next_index<len(a.layers) else None
    consumed= startup if selected is None else mass_g(selected.cumulative_mm,material,diameter,density_g_cm3)
    return Plan(True,None if selected is None else selected.index,next_index,boundary,z,total,remaining_g,reserve_g,usable,consumed,usable-consumed)
