"""Right-hand silhouette of the bow photo from strake to boot-top: strake outer edge (dark band) then hull edge."""
import json, numpy as np
from PIL import Image
D = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/photo"
a = np.asarray(Image.open(f"{D}/up/IMG_9388.png").convert("RGB")).astype(float)
R, G, B = a[..., 0], a[..., 1], a[..., 2]; L = a.mean(2)
hull = (L > 165) & (np.abs(R - B) < 14) & (np.abs(G - B) < 14)
dark = L < 70
out = []
for v in range(0, 812, 2):
    xs = np.arange(1160, 900, -1)
    # strake: first dark pixel from right
    d = np.nonzero(dark[v, xs])[0]
    h = np.nonzero(hull[v, xs])[0]
    ud = xs[d[0]] if len(d) else -1
    uh = -1
    # hull edge: first run of >=5 consecutive hull pixels
    for k in h:
        if k + 5 < len(xs) and hull[v, xs[k:k + 5]].all():
            uh = xs[k]; break
    out.append([v, int(ud), int(uh)])
out = np.array(out)
# silhouette = outermost of (strake dark edge, hull edge) where dark edge within 40 px of hull edge
sil = []
for v, ud, uh in out:
    cands = [c for c in (ud, uh) if c > 0]
    if ud > 0 and uh > 0 and ud - uh > 40:
        cands = [uh]
    if cands:
        sil.append([v, max(cands), ud, uh])
sil = np.array(sil)
json.dump({"right_sil": sil.tolist()}, open(f"{D}/m9388_rsil.json", "w"))
for v in range(400, 812, 20):
    i = np.argmin(abs(sil[:, 0] - v)); print("v %d sil %d (dark %d, hull %d)" % tuple(sil[i]))
