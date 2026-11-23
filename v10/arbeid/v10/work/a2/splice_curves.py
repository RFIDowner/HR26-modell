"""Skjoeter inn den nye spantfamilien i curves.py (beholder CRLF)."""
import sys
WT = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/lines"
A2 = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/work/a2"
fn = WT + "/hr26/curves.py"
src = open(fn, "rb").read().decode("utf-8").replace("\r\n", "\n")
block = open(A2 + "/block_section.py", encoding="utf-8").read()

a = src.index("# --------------------------------------------------- tverrsnittets tabeller")
b = src.index("def section_inner(")
src = src[:a] + block.rstrip("\n") + "\n\n\n" + src[b:]

vol_new = '''def displaced_volume_m3(n_stations: int = 200) -> float:
    """Kanobunnens volum under DWL (uten kjol og ror), ved integrasjon av
    spantarealene til spantformen i section()."""
    xs = np.linspace(P.LWL_FWD, max(P.LWL_AFT, P.TRANSOM_WL_X), n_stations)
    area = []
    for x in xs:
        p = _section_geom(float(x))["pts"]
        if p[0, 1] >= -1.0:
            area.append(0.0)
            continue
        zz = np.linspace(p[0, 1], 0.0, 80)
        yy = np.interp(zz, p[:, 1], p[:, 0])
        area.append(2.0 * float(np.trapezoid(yy, zz)))
    return float(np.trapezoid(area, xs)) / 1e9
'''
a = src.index("def displaced_volume_m3(")
src = src[:a] + vol_new
if "import math\n" not in src:
    src = src.replace("import csv\n", "import csv\nimport math\n", 1)
open(fn, "wb").write(src.replace("\n", "\r\n").encode("utf-8"))
print("ok", src.count("\n"), "lines")
