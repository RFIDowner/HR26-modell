"""Render panels: flat / smooth / zebra, same camera. argv: name stl_path mode(ours|loft|bambu) [W]"""
import sys, time
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/surface")
from common import *
from PIL import Image
name, path, kind = sys.argv[1], sys.argv[2], sys.argv[3]
W = int(sys.argv[4]) if len(sys.argv) > 4 else 640
AZ = float(sys.argv[5]) if len(sys.argv) > 5 else 140.0
EL = float(sys.argv[6]) if len(sys.argv) > 6 else 12.0
STRIPE = float(sys.argv[7]) if len(sys.argv) > 7 else 4.0
TAG = sys.argv[8] if len(sys.argv) > 8 else ""
T32 = load_raw(path)
V, F = weld(T32)
if kind == "ours":
    V = rotz(V, -45.0); V[:, 1] -= 0.5 * (V[:, 1].max() + V[:, 1].min())
    lab = components(len(V), F); ul, cnt = np.unique(lab, return_counts=True)
    F = F[lab == ul[np.argmax(cnt)]]                 # drop interior cavities
elif kind == "bambu":
    V = V * 0.3708
    c = V[F].mean(1)
    F = F[(c[:, 2] < 3 * 0.3708) & (V[F][:, :, 2].max(1) < 6 * 0.3708)]   # drop rails, pulpits, mast, boom
fn, area = face_normals(V, F)
ok = area > 1e-12
F, fn = F[ok], fn[ok]
cn = corner_normals(V, F, fn)
R = look(AZ, EL)
t = time.time()
rr = raster(V, F, R, W)
print(name, "faces", len(F), "raster %.1fs" % (time.time() - t))
for mode in ("flat", "smooth", "zebra"):
    Image.fromarray(shade2(rr, fn, cn, R, mode, stripe_deg=STRIPE)).save(OUT + f"/panel_{name}{TAG}_{mode}.png")
