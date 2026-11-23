import sys; sys.path.insert(0, '.')
import numpy as np
import common as c
C, P = c.C, c.P

ux, ud = C._read("uw_station.csv", "x_from_bow_mm", "depth_below_DWL_mm")
uz = -ud

def e_profile():
    """Enderlein centreline profile below the stem head: z(x) lower envelope of hull_* segments."""
    segs = ["hull_stem", "hull_fwd_bottom", "hull_keel_le", "hull_keel_bottom", "hull_te", "hull_te_fillet", "hull_aft_bottom"]
    pts = np.vstack([c.eline(s) for s in segs])
    return pts

E = e_profile()
def e_z(x, half=15.0):
    m = np.abs(E[:, 0] - x) < half
    return np.nan if not m.any() else float(E[m, 1].min())

def u_z(x, half=12.0):
    m = np.abs(ux - x) < half
    return np.nan if not m.any() else float(uz[m].min())

stem = c.eline("hull_stem")
def e_stem_x(z):
    s = stem[np.argsort(stem[:, 1])]
    return float(np.interp(z, s[:, 1], s[:, 0]))

print("x     model  broch(uw)  E    E-40   E-M   E-40-B   M-B")
for x in [600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1600, 1800, 2000, 2200, 2400, 2600, 2800, 3000, 3200, 3300,
          5800, 5900, 6000, 6200, 6400, 6600, 6800, 7000, 7200, 7400, 7500, 7600, 7700, 7760]:
    m = C.bottom_z(x); b = u_z(x); e = e_z(x)
    print(f"{x:5d} {m:7.1f} {b:7.1f} {e:7.1f} {e-40:7.1f} {e-m:6.1f} {e-40-b:7.1f} {m-b:6.1f}")
print("stem x at z (E, E with z_model=z_E-40 i.e. x_E(z+40), model):")
for z in [600, 400, 200, 100, 0, -50, -100]:
    # model stem x at z: invert bottom_z on x<1400
    xs = np.linspace(0, 1500, 3001); zs = np.array([C.bottom_z(v) for v in xs])
    xm = float(np.interp(-z, -zs, xs))
    print(f"  z {z:5d}: E {e_stem_x(z):7.1f}  E(+40) {e_stem_x(z+40):7.1f}  model {xm:7.1f}")
