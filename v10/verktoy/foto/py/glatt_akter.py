"""Glatthetskontroll akter (trinn 4, 13.11.2026): vannlinjer i plan og spant
for HEAD og en tilpasning fra opt_hjorne (out/opt_hjorne_<tag>.json).
Vannlinjene klippes ved akterspeilet. Skriver et bilde og et maal paa
krusninger: storste fortegnsskifte i krumningen langs hver vannlinje.

Kjoeres fra denne mappa: python glatt_akter.py TAG UT.png
"""
import json
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import common as c, uwlib as U, hjerte as Hj

tag, out = sys.argv[1], sys.argv[2]
fit = json.load(open(c.W + "/out/opt_hjorne_%s.json" % tag))
over = {k: [tuple(p) for p in v] for k, v in fit["params"].items()}

XS = np.arange(5000.0, 7960.0, 10.0)
ZW = (-300.0, -200.0, -100.0, 0.0, 100.0, 200.0, 300.0)
XSEC = (6000.0, 6600.0, 7000.0, 7300.0, 7550.0, 7750.0)


def wl(C, z):
    ys = []
    for x in XS:
        if x > U.transom_x(z, 0.0) + 1.0:
            ys.append(np.nan)
            continue
        p = C._section_geom(float(x))["pts"]
        zz = np.maximum.accumulate(p[:, 1])
        ys.append(np.nan if z <= zz[0] else float(np.interp(z, zz, p[:, 0])))
    y = np.array(ys)
    # klipp ved akterspeilet (x <= transom_x(z, y))
    y[XS > np.array([U.transom_x(z, yy if np.isfinite(yy) else 0.0) for yy in y])] = np.nan
    return y


def wiggle(y):
    """Antall fortegnsskifter i krumningen og stoerste |krumning| (1/m)."""
    ok = np.isfinite(y)
    yy = y[ok]
    if len(yy) < 9:
        return 0, 0.0
    k = np.diff(yy, 2) / 10.0 ** 2 * 1000.0
    k = np.convolve(k, np.ones(5) / 5, mode="valid")
    s = np.sign(k[np.abs(k) > 0.05])
    return int(np.sum(s[1:] != s[:-1])), float(np.max(np.abs(k)))


fig, ax = plt.subplots(1, 2, figsize=(15, 6.5), gridspec_kw=dict(width_ratios=[1.6, 1]))
res = {}
for lab, ov, ls in (("HEAD", {}, "--"), (tag, over, "-")):
    C = Hj.apply(ov)
    for i, z in enumerate(ZW):
        y = wl(C, z)
        w = wiggle(y)
        res.setdefault(lab, {})[z] = w
        ax[0].plot(XS, y, ls, color=plt.cm.viridis(i / (len(ZW) - 1)), lw=1.3,
                   label=f"z {z:+.0f}" if lab == tag else None)
    for j, x in enumerate(XSEC):
        p = np.array(C.section(float(x), 200))
        ax[1].plot(p[:, 0], p[:, 1], ls, color=plt.cm.plasma(j / (len(XSEC))), lw=1.3,
                   label=f"x {x:.0f}" if lab == tag else None)
    cyz = np.array(fit["cyz"]) if lab == tag else None
hj = json.load(open(c.W + "/out/hjorne9391.json"))
for k in ("left", "right"):
    r = hj["res"][k]
    ax[1].plot([q["y_photo"] for q in r], [q["z"] for q in r], "o", ms=4, color="#2060ff",
               label="eierens prikker (paa akterspeilet)" if k == "left" else None)
ax[1].plot(cyz[:, 0], cyz[:, 1], "-", color="#2060ff", lw=2.5, alpha=0.5, label="hjoernet, tilpasset")
ax[0].set_title("Vannlinjer akter (stiplet: HEAD, hel: %s)" % tag)
ax[0].set_xlabel("x (mm fra baugen)"); ax[0].set_ylabel("halvbredde y (mm)")
ax[0].legend(fontsize=8, ncol=2); ax[0].grid(alpha=0.3)
ax[1].set_title("Spant (stiplet: HEAD)"); ax[1].set_aspect("equal"); ax[1].grid(alpha=0.3)
ax[1].set_xlim(0, 1000); ax[1].set_ylim(-450, 900); ax[1].legend(fontsize=7)
fig.tight_layout(); fig.savefig(out, dpi=90)
for lab, d in res.items():
    print(lab, {int(z): v for z, v in d.items()})
