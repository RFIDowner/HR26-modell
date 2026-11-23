"""Volume, waterline and topside numbers for candidate section tables (analytic, no CAD).
Monkeypatches the snapshot curves module; the repo is not touched."""
import sys, json
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/11dad074fa1abe1e/d28ff77b-a16b-454a-a3fa-4f83bd19bf4c/scratchpad/undervann/py")
import numpy as np
import uw
C, P = uw.C, uw.P

def hb_at(x, z):
    p = C._section_geom(float(x))["pts"]
    if z < p[0, 1]:
        return 0.0
    return float(np.interp(z, p[:, 1], p[:, 0]))

def numbers():
    xs = np.linspace(P.LWL_FWD, P.TRANSOM_WL_X, 300)
    wl = np.array([C.wl_half_breadth(float(x)) for x in xs])
    out = dict(vol=C.displaced_volume_m3(), bwl=2 * wl.max(), x_bwl=float(xs[wl.argmax()]))
    out["z130"] = {x: round(hb_at(x, 130.0)) for x in (1200, 1500, 1800, 2100, 2400)}
    out["wl"] = {x: round(C.wl_half_breadth(float(x))) for x in (2000, 3000, 4000, 5000, 6000, 7000, 7600)}
    # topside change above the strake vs today: max |dy| over z in [strake, sheer-30]
    return out

def set_tables(dead=None, nexp=None, flare=None):
    C._DEADRISE = C._pchip(dead or P.SECTION_DEADRISE)
    C._NEXP = C._pchip(nexp or P.SECTION_N)
    C._FLARE = C._pchip(flare or P.SECTION_FLARE)
    C._GEOM.clear()

def topside_dev(ref):
    d = 0.0
    for x in np.arange(1000, 7700, 250):
        p = C._section_geom(float(x))["pts"]
        zs, zk = C.sheer_z(x), C.strake_z(x)
        for z in np.linspace(zk, zs - 30, 6):
            d = max(d, abs(float(np.interp(z, p[:, 1], p[:, 0])) - ref[(x, round(z, 1))]))
    return d

CANDS = {
 "today": dict(),
 "B_dead_aft": dict(dead=[(0.00, 45.0), (0.127, 24.0), (0.20, 18.0), (0.30, 14.0), (0.50, 12.0), (0.75, 12.0), (1.00, 13.0)]),
 "C_dead_aft_n2.6": dict(dead=[(0.00, 45.0), (0.127, 24.0), (0.20, 18.0), (0.30, 14.0), (0.50, 12.0), (0.75, 12.0), (1.00, 13.0)],
                        nexp=[(0.00, 2.2), (0.15, 2.5), (0.35, 2.6), (0.60, 2.6), (0.80, 2.5), (1.00, 2.4)]),
 "D_dead_aft_n2.3": dict(dead=[(0.00, 45.0), (0.127, 26.0), (0.20, 20.0), (0.30, 16.0), (0.50, 14.0), (0.75, 14.0), (1.00, 15.0)],
                        nexp=[(0.00, 2.1), (0.15, 2.2), (0.35, 2.3), (0.60, 2.3), (0.80, 2.25), (1.00, 2.2)]),
 "E_n_only_2.6": dict(nexp=[(0.00, 2.2), (0.15, 2.5), (0.35, 2.6), (0.60, 2.6), (0.80, 2.5), (1.00, 2.4)]),
}
if __name__ == "__main__":
    set_tables()
    ref = {}
    for x in np.arange(1000, 7700, 250):
        p = C._section_geom(float(x))["pts"]
        zs, zk = C.sheer_z(x), C.strake_z(x)
        for z in np.linspace(zk, zs - 30, 6):
            ref[(x, round(z, 1))] = float(np.interp(z, p[:, 1], p[:, 0]))
    res = {}
    for k, v in CANDS.items():
        set_tables(**v)
        n = numbers(); n["topside_maxdev_above_strake"] = round(topside_dev(ref), 1)
        res[k] = n
        print(k, json.dumps(n))
    uw.save_json(dict(cands={k: {kk: str(vv) for kk, vv in v.items()} for k, v in CANDS.items()}, numbers=res), uw.OUT + "/candidates.json")
