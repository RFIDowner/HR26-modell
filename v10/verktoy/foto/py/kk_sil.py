"""kk_: oevre silhuett akter (karm/akterdekk) i nye (4) og nye (6) mot modellen.

For hver bildekolonne: bildets oeverste "baathvite" piksel (lang nok rad
nedover) mot modellens oeverste piksel i en render med samme kamera. Avviket
korrigeres med fenderlistens avvik (bilde - modell) ved samme x, saa en
loddrett kamerafeil faller bort, og tilbakeprojiseres til planet y = y_modell
(silhuettpunktets sideposisjon) -> dz i mm.

  python ../../../../tools/memcap.py --gb 3 -- python kk_sil.py <scratch> n4|n6

Ut: out/kk_sil_<bilde>.json, <scratch>/kk_sil_<bilde>.png (kontrollbilde).
"""
import json
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

import common as c
import geo9374 as G
G.use_model(None)
import kk_lib as L
from hr26 import deckhouse as D

P, C = c.P, c.C
SP, WHICH = sys.argv[1], sys.argv[2]
S = 2.0

if WHICH == "n4":
    import n4_ovl as O
    import n4_cam as K
    cam, _ = O.load("fprof:pin_Nc_f850")
    IMG = O.IMG
    T = json.load(open(c.W + "/out/n4_trace.json"))
    ST3 = K.STRAKE3
    U0, U1, VSTART, RUN = 838, 1012, 300, 5
    BOX = (800, 300, 1030, 450)
else:
    import n6_cam as K
    import n6_geo as N
    J = json.load(open(c.W + "/out/n6_cam.json"))
    MODE = sys.argv[3] if len(sys.argv) > 3 else "pin_keel"
    d = J["modes"][MODE]
    cam = K.make_cam(np.asarray(d["q"], float), d["cfg"]["mode"])
    IMG = c.FOTO + "/nye (6).jpeg"
    T = json.load(open(c.W + "/out/n6_trace.json"))
    ST3 = N.strake_paths()["side"]
    U0, U1, VSTART, RUN = 215, 760, 590, 7
    BOX = (150, 560, 900, 760)

ph = np.asarray(Image.open(IMG).convert("RGB")).astype(float)
R_, G_, B_ = ph[..., 0], ph[..., 1], ph[..., 2]
boat = (R_ > 172) & (G_ > 158) & (B_ < R_ + 4) & ((R_ - B_) < 70)

V, F = L.model_mesh()
img, XYZ = L.render(cam, V, F, scale=S)
bgm = ~np.isfinite(XYZ[..., 0])


def photo_top(u):
    col = boat[:, u]
    for v in range(VSTART, ph.shape[0] - RUN):
        if col[v:v + RUN].all():
            # subpiksel: halvveis i lysovergangen over v
            g = ph[v - 3:v + 2, u].mean(1)
            return v - 0.5
    return np.nan


def model_top(u):
    uu = int(round((u + 0.5) * S))
    col = ~bgm[:, uu]
    i = int(np.argmax(col[int(VSTART * S):])) + int(VSTART * S)
    if not col[i]:
        return np.nan, None
    return i / S, XYZ[i + 1, uu]


st = np.asarray(T["strake"], float)
st_u, st_v = st[:, 0], st[:, 3]
us, vs, _ = cam.project(ST3)


def strake_resid_at_x(x):
    """bilde - modell for listens senter der modellens liste har dette x."""
    k = int(np.argmin(np.abs(ST3[:, 0] - x)))
    u_m, v_m = us[k], vs[k]
    if u_m < st_u.min() or u_m > st_u.max():
        return np.nan, u_m
    return float(np.interp(u_m, st_u, st_v) - v_m), u_m


rows = []
for u in range(U0, U1 + 1):
    vp = photo_top(u)
    vm, Xm = model_top(u)
    if Xm is None or not np.isfinite(vp):
        continue
    rows.append([u, vp, vm, *Xm])
A = np.array(rows, float)
# fittings (vinsj, klamper, pulpit): median over 9 kolonner
vp_f = ndi.median_filter(A[:, 1], 9, mode="nearest")
vm_f = ndi.median_filter(A[:, 2], 9, mode="nearest")
res = []
for i, (u, vp, vm, x, y, z) in enumerate(A):
    r, _ = strake_resid_at_x(x)
    # tilbakeprojiser bildets (korrigerte) silhuett til planet y = y_modell
    vpc = vp_f[i] - (r if np.isfinite(r) else 0.0)
    ray = np.array([(u + 0.5 - cam.cx) / cam.f, (vpc - cam.cy) / cam.f, 1.0]) @ cam.R
    t = (y - cam.C[1]) / ray[1]
    Xp = cam.C + t * ray
    rayr = np.array([(u + 0.5 - cam.cx) / cam.f, (vp_f[i] - cam.cy) / cam.f, 1.0]) @ cam.R
    Xr = cam.C + (y - cam.C[1]) / rayr[1] * rayr
    res.append(dict(u=float(u), v_photo=float(vp_f[i]), v_model=float(vm_f[i]), x=float(x), y=float(y),
                    z_model=float(z), strake_resid_px=float(r), z_photo=float(Xp[2]), z_photo_raw=float(Xr[2]),
                    x_photo=float(Xp[0]), dz=float(Xp[2] - z), dz_raw=float(Xr[2] - z)))

# tabell per 100 mm i x
xs = np.array([r["x"] for r in res])
print("bilde", WHICH, "kamera", np.round(cam.C), "f %.0f" % cam.f)
print("   x   z_mod  z_foto  dz   (ukorr dz)  liste-avvik px   u")
tab = []
for X in range(5400, 8001, 100):
    s = np.abs(xs - X) < 50
    if s.sum() < 2:
        continue
    zm = np.median([res[i]["z_model"] for i in np.where(s)[0]])
    zp = np.median([res[i]["z_photo"] for i in np.where(s)[0]])
    dzr = np.median([res[i]["dz_raw"] for i in np.where(s)[0]])
    rr = np.median([res[i]["strake_resid_px"] for i in np.where(s)[0]])
    uu = np.median([res[i]["u"] for i in np.where(s)[0]])
    yy = np.median([res[i]["y"] for i in np.where(s)[0]])
    tab.append(dict(x=X, y=float(yy), z_model=float(zm), z_photo=float(zp), dz=float(zp - zm), dz_raw=float(dzr),
                    strake_px=float(rr), u=float(uu), n=int(s.sum())))
    print("%5d %6.0f %6.0f %5.0f  (%5.0f)   %5.1f   %4.0f  y %5.0f n %d" % (X, zm, zp, zp - zm, dzr, rr, uu, yy, s.sum()))
c.save_json(dict(image=WHICH, cam_C=cam.C, f=cam.f, table=tab, cols=res), c.W + "/out/kk_sil_%s.json" % WHICH)

# kontrollbilde
Z = 4
im = Image.open(IMG).convert("RGB").crop(BOX)
im = im.resize((im.width * Z, im.height * Z), Image.LANCZOS)
dr = ImageDraw.Draw(im)


def P2(u, v):
    return ((u + 0.5 - BOX[0]) * Z, (v - BOX[1]) * Z)


dr.line([P2(r["u"], r["v_model"]) for r in res], fill=(255, 0, 0), width=2)
dr.line([P2(r["u"], r["v_photo"]) for r in res], fill=(0, 255, 0), width=2)
dr.line([P2(a, b) for a, b in zip(us, vs) if BOX[0] < a < BOX[2]], fill=(255, 0, 255), width=1)
im.save(SP + "/kk_sil_%s.png" % WHICH)
