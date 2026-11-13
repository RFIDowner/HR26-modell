"""kant3.jpeg (gammelt papirbilde, styrbord side naer, baugen til hoeyre):
spor per kolonne u
  band_top   overkant av det moerke (groenne) baandet (lys -> moerk)
  band_bot   underkant av baandet (moerk -> den hvite linja over listen)
  strake     listens moerke senter (under den hvite linja)
  crest      den lyse toppen (dekkskantens hoeylys) over baandet
og skriv ../out/kd_k3.json. Ingen kamera (ukjent); forholdene brukes.

  python ../../../../tools/memcap.py --gb 3 -- python kd_k3.py
"""
import numpy as np
from PIL import Image

import common as c

IMG = c.FOTO + "/kant3.jpeg"


def trace():
    im = np.asarray(Image.open(IMG).convert("RGB"), float)
    Lm = im.mean(2)
    H, W = Lm.shape
    rows = []
    for u in range(4, W - 4, 2):
        col = Lm[:, u - 2:u + 3].mean(1)
        # baandet: foerste lange moerke strekning (L < 60) under rad 400
        dark = col < 60
        r0 = None
        for r in range(400, 600):
            if dark[r] and dark[r:r + 6].all():
                r0 = r
                break
        if r0 is None:
            continue
        # subpiksel: 50 %-kryssing mellom lys over og moerk
        hi = np.median(col[r0 - 14:r0 - 6])
        lo = np.median(col[r0 + 2:r0 + 8])
        thr = 0.5 * (hi + lo)
        r = r0
        while r > r0 - 10 and col[r] < thr:
            r -= 1
        bt = r + (col[r] - thr) / max(col[r] - col[r + 1], 1e-6)
        if not (r0 - 10 < bt < r0 + 2):
            continue
        # underkant: moerk -> lys (den hvite linja), saa listens moerke
        r1 = r0
        while r1 < 620 and col[r1] < 90:
            r1 += 1
        # den hvite linja: lokalt maks rett under
        wl = r1 + int(np.argmax(col[r1:r1 + 8]))
        # listen: minimum under den hvite linja
        st = wl + 2 + int(np.argmin(col[wl + 2:wl + 26]))
        # listens moerke senter som tyngdepunkt av (terskel - L)
        seg = col[wl + 1:wl + 30]
        thr2 = 0.5 * (col[wl] + col[st])
        w = np.clip(thr2 - seg, 0, None)
        stc = wl + 1 + float((w * np.arange(len(seg))).sum() / max(w.sum(), 1e-6))
        # hoeylyset over baandet: maks i 30 px over
        a = max(int(bt) - 32, 0)
        cr = a + int(np.argmax(col[a:int(bt) - 2]))
        rows.append(dict(u=u, band_top=float(bt), band_bot=float(r1), white=float(wl), strake=stc, crest=float(cr),
                         crest_L=float(col[cr])))
    return rows


if __name__ == "__main__":
    R = trace()
    c.save_json(dict(image="kant3.jpeg", rows=R), c.W + "/out/kd_k3.json")
    for r in R[::10]:
        print("u %3d  crest %5.1f  band_top %6.1f  band_bot %5.1f  hvit %5.1f  liste %6.1f  baand %5.1f  topp-liste %5.1f"
              % (r["u"], r["crest"], r["band_top"], r["band_bot"], r["white"], r["strake"], r["band_bot"] - r["band_top"],
                 r["strake"] - r["band_top"]))
