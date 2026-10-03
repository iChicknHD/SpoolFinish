import argparse
from pathlib import Path
from .parser import analyze_text, GcodeError
from .planner import plan_change, PlanError
from .patcher import default_output, patch
from .material import DEFAULT_DIAMETER_MM

def main(argv=None):
    ap=argparse.ArgumentParser(prog="spoolfinish")
    sub=ap.add_subparsers(dest="command",required=True)
    a=sub.add_parser("analyze"); a.add_argument("source",type=Path); a.add_argument("--remaining",type=float,required=True); a.add_argument("--reserve",type=float,default=0); a.add_argument("--material",choices=("PLA","PETG","ABS","ASA"),default="PLA"); a.add_argument("--diameter",type=float,default=DEFAULT_DIAMETER_MM); a.add_argument("--density",type=float,help="material density override in g/cm^3"); a.add_argument("--firmware",choices=("marlin","klipper"),default="marlin"); a.add_argument("--output",type=Path)
    ns=ap.parse_args(argv)
    try:
        analysis=analyze_text(ns.source.read_text(encoding="utf-8"))
        plan=plan_change(analysis,ns.remaining,ns.reserve,ns.material,ns.diameter,ns.density)
        output=None
        if plan.change_required:
            output=patch(ns.source,ns.output or default_output(ns.source),plan,ns.firmware)
        values={"TOTAL_REQUIRED_G":plan.total_g,"AVAILABLE_G":plan.available_g,"RESERVE_G":plan.reserve_g,"USABLE_G":plan.usable_g,"CHANGE_REQUIRED":"YES" if plan.change_required else "NO","SAFE_CHANGE_LAYER":"" if plan.change_before_layer is None else plan.change_before_layer,"SAFE_CHANGE_Z_MM":"" if plan.change_z is None else plan.change_z,"CONSUMED_BEFORE_CHANGE_G":plan.consumed_before_g,"EXPECTED_REMAINDER_G":plan.remainder_g,"OUTPUT":"" if output is None else output}
        for k,v in values.items(): print(f"{k}={v:.2f}" if isinstance(v,float) else f"{k}={v}")
        return 0
    except (OSError,UnicodeError,GcodeError,PlanError,ValueError) as e:
        print(f"ERROR={e}"); return 2
if __name__=="__main__": raise SystemExit(main())
