"""Foer/etter-nærbilder. argv: before.stl after.stl out_prefix"""
import sys, math, time
import numpy as np
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/work/b")
from common import load_raw, weld, components, face_normals, corner_normals, look, raster, shade2
from PIL import Image, ImageDraw, ImageFont

def prep(path):
    T = load_raw(path).astype(np.float64)
    V, F = weld(T.astype(np.float32))
    V = V.copy()
    V[:, 0] -= V[:, 0].min(); V[:, 1] -= 0.5 * (V[:, 1].max() + V[:, 1].min()); V[:, 2] -= V[:, 2].min()
    V *= 30.0; V[:, 0] += 4.0; V[:, 2] -= 1400.0
    lab = components(len(V), F); ul, cnt = np.unique(lab, return_counts=True)
    F = F[lab == ul[np.argmax(cnt)]]
    fn, area = face_normals(V, F)
    ok = area > 1e-9
    return V, F[ok], fn[ok]

VIEWS = [  # navn, az, el, boks (xmin,xmax,ymin,ymax,zmin,zmax), bredde px
    ("hekk_akterfra", 0.0, 4.0, (7300, 8100, -1400, 1400, -400, 1300), 760),
    ("hekk_skraatt_akter", 38.0, 10.0, (6900, 8100, -200, 1400, -450, 1300), 760),
    ("hekk_ovenfra_akter", 30.0, 38.0, (6700, 8100, -1400, 1400, -450, 1400), 760),
    ("liste_side", 90.0, 4.0, (0, 8000, 0, 1400, 300, 1400), 1500),
    ("liste_baug", 135.0, 8.0, (0, 1300, -50, 700, 700, 1350), 760),
    ("kjolrot", 75.0, -12.0, (3000, 6400, -100, 900, -900, -250), 760),
]

def render(V, F, fn, az, el, box, W, lo_hi=None):
    c = V[F].mean(1)
    sel = (c[:, 0] > box[0]) & (c[:, 0] < box[1]) & (c[:, 1] > box[2]) & (c[:, 1] < box[3]) & (c[:, 2] > box[4]) & (c[:, 2] < box[5])
    F2, fn2 = F[sel], fn[sel]
    cn = corner_normals(V, F2, fn2)
    R = look(az, el)
    rr = raster(V, F2, R, W, bbox=lo_hi)
    return shade2(rr, fn2, cn, R, "smooth"), rr

def bbox_of(Vs, Fs, az, el, box):
    R = look(az, el)
    los, his = [], []
    for V, F in zip(Vs, Fs):
        c = V[F].mean(1)
        sel = (c[:, 0] > box[0]) & (c[:, 0] < box[1]) & (c[:, 1] > box[2]) & (c[:, 1] < box[3]) & (c[:, 2] > box[4]) & (c[:, 2] < box[5])
        P = V[np.unique(F[sel])] @ R.T
        los.append(P[:, :2].min(0)); his.append(P[:, :2].max(0))
    return np.min(los, 0), np.max(his, 0)

if __name__ == "__main__":
    before, after, pre = sys.argv[1], sys.argv[2], sys.argv[3]
    only = sys.argv[4].split(",") if len(sys.argv) > 4 else None
    A = prep(before); B = prep(after)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 22)
    except Exception:
        font = ImageFont.load_default()
    for name, az, el, box, W in VIEWS:
        if only and name not in only:
            continue
        t = time.time()
        lohi = bbox_of([A[0], B[0]], [A[1], B[1]], az, el, box)
        Wp = min(W, 800) if W < 1000 else 1580
        ims = []
        for (V, F, fn), lab in ((A, "foer (i dag)"), (B, "V10 pakke B")):
            img, _ = render(V, F, fn, az, el, box, Wp, lohi)
            im = Image.fromarray(img); d = ImageDraw.Draw(im); d.text((10, 6), lab, fill=(200, 30, 30), font=font)
            ims.append(im)
        if W >= 1000:      # stablet over hverandre
            out = Image.new("RGB", (ims[0].width, ims[0].height + ims[1].height), (255, 255, 255))
            out.paste(ims[0], (0, 0)); out.paste(ims[1], (0, ims[0].height))
        else:
            out = Image.new("RGB", (ims[0].width + ims[1].width, max(ims[0].height, ims[1].height)), (255, 255, 255))
            out.paste(ims[0], (0, 0)); out.paste(ims[1], (ims[0].width, 0))
        if out.width > 1600:
            out = out.resize((1600, int(out.height * 1600 / out.width)), Image.LANCZOS)
        out.save(f"{pre}_{name}.png")
        print(name, "%.1fs" % (time.time() - t), out.size)
