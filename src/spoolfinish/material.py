import math
DENSITIES_G_CM3={"PLA":1.24,"PETG":1.27,"ABS":1.04,"ASA":1.07}
DEFAULT_DIAMETER_MM=1.75
def mass_g(length_mm: float, material: str, diameter_mm: float=DEFAULT_DIAMETER_MM, density_g_cm3: float|None=None)->float:
    if length_mm<0 or diameter_mm<=0: raise ValueError("length must be nonnegative and diameter positive")
    density=density_g_cm3 if density_g_cm3 is not None else DENSITIES_G_CM3.get(material.upper())
    if density is None or density<=0: raise ValueError(f"unsupported material/density: {material}")
    return length_mm*math.pi*(diameter_mm/2)**2/1000*density
def length_mm(mass: float, material: str, diameter_mm: float=DEFAULT_DIAMETER_MM)->float:
    return mass/mass_g(1.0,material,diameter_mm)
