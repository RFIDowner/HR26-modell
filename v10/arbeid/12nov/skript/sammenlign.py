"""Foto | V10 | Bambu med samme kamera (kameraene fra score.py, PHOTO_VIEWS).
python sammenlign.py <score.py> <v10.stl (baatramme fra build_hull_only)> <bambu.stl> <foto-mappe> <ut.png> [visninger]
visninger: kommaliste av IMG_9370,IMG_9389,IMG_9391,IMG_9388 (standard IMG_9370,IMG_9391)"""
import importlib.util, math, os, sys
import numpy as np
from PIL import Image, ImageOps, ImageDraw

spec = importlib.util.spec_from_file_location("score", sys.argv[1])
SC = importlib.util.module_from_spec(spec); spec.loader.exec_module(SC)
v10_path, bambu_path, photo_dir, out = sys.argv[2:6]
views = (sys.argv[6] if len(sys.argv) > 6 else "IMG_9370,IMG_9391").split(",")

def mesh(T):
    V, F = SC.weld(T, 1e-4)
    A, B, C = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    n = np.cross(B - A, C - A)
    fn = n / np.maximum(np.linalg.norm(n, axis=1), 1e-30)[:, None]
    return V, F, fn

# V10: modell-mm, x=0 ved baugspissen (stasjon x=4), kjolen paa z=0
T, _ = SC.load_stl(v10_path)
T = T * 30.0
T[:, :, 0] += 4.0
T[:, :, 2] -= 1400.0
ours = mesh(T)

# Bambu: skala og hoyde som i V10-analysen (robot/edges/lib.py, bambu_full uten strekk)
Tb, _ = SC.load_stl(bambu_path)
k = 0.3708
Tb = Tb * k
Tb[:, :, 2] = Tb[:, :, 2] + 37.4 * k + 83.1
Tb = Tb * 30.0
Tb[:, :, 2] -= 1400.0
Vb = Tb.reshape(-1, 3)
Tb[:, :, 1] -= 0.5 * (Vb[:, 1].max() + Vb[:, 1].min())
# baugen: den smale enden oppe ved dekket
x0, x1 = Vb[:, 0].min(), Vb[:, 0].max()
w_lo = np.abs(Vb[Vb[:, 0] < x0 + 0.08 * (x1 - x0), 1]).max()
w_hi = np.abs(Vb[Vb[:, 0] > x1 - 0.08 * (x1 - x0), 1]).max()
print("Bambu-ender: bredde ved min x", round(w_lo), "ved max x", round(w_hi))
if w_hi < w_lo:                       # baugen ved stor x: snu
    Tb[:, :, 0] = -Tb[:, :, 0]
    Tb[:, :, 1] = -Tb[:, :, 1]
    Tb = Tb[:, ::-1, :]
Vb = Tb.reshape(-1, 3)
Tb[:, :, 0] += 4.0 - Vb[:, 0].min()
bam = mesh(Tb)
print("Bambu x", Tb[:, :, 0].min().round(0), Tb[:, :, 0].max().round(0), "y", Tb[:, :, 1].max().round(0),
      "z", Tb[:, :, 2].min().round(0), Tb[:, :, 2].max().round(0))

rows = []
for vname in views:
    pv = next(p for p in SC.PHOTO_VIEWS if p["file"].startswith(vname))
    im = ImageOps.exif_transpose(Image.open(os.path.join(photo_dir, pv["file"]))).convert("RGB")
    W, H = im.size
    xa, ya, xb, yb = pv["crop"]
    k_ = 620.0 / (xb - xa)
    cw, ch = round((xb - xa) * k_), round((yb - ya) * k_)
    R = SC.rot_from_euler(pv["yaw"], pv["pitch"], pv["roll"])
    cam = SC.Cam(pv["C"], R, cw, ch, f=pv["f"] * k_, cx=(W / 2.0 - xa) * k_, cy=(H / 2.0 - ya) * k_)
    ph = im.crop((xa, ya, xb, yb)).resize((cw, ch), Image.LANCZOS)
    r1, _ = SC.render_view(cam, *ours, ss=2)
    r2, _ = SC.render_view(cam, *bam, ss=2)
    rows.append((pv, ph, r1, r2))

pad, head = 8, 26
Wt = 3 * 620 + 4 * pad
Ht = sum(r[1].size[1] + head + pad for r in rows) + pad
sheet = Image.new("RGB", (Wt, Ht), (255, 255, 255))
d = ImageDraw.Draw(sheet)
y = pad
for pv, ph, r1, r2 in rows:
    for i, (img, lab) in enumerate(((ph, "Foto " + pv["file"][:8]), (r1, "V10"), (r2, "Bambu (AI)"))):
        x = pad + i * (620 + pad)
        d.text((x, y + 4), lab, fill=(20, 20, 20), font=SC._font(16, bold=True))
        sheet.paste(img, (x, y + head))
    y += head + ph.size[1] + pad
sheet.save(out)
print(out, sheet.size)
