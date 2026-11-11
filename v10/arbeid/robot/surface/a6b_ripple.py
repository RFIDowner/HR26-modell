import sys, math
import numpy as np
from scipy.interpolate import make_smoothing_spline
OUT = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/surface"
res = np.load(OUT + "/ripple.npy", allow_pickle=True).item()
xs_st = np.load(OUT + "/stations.npy")
def lam_for(lc, dx=5.0):
    return (lc / (2 * math.pi)) ** 4 / dx
out = {}
for z, R in res.items():
    x, y = R["x"], R["y"]
    for lc in (1200.0, 600.0):
        sp = make_smoothing_spline(x, y, lam=lam_for(lc))
        r = y - sp(x)
        mid = (x > 1500) & (x < 7000)
        rr = r[mid] - r[mid].mean()
        F = np.abs(np.fft.rfft(rr * np.hanning(len(rr)))); fr = np.fft.rfftfreq(len(rr), 5.0)
        k = np.argmax(F[1:]) + 1
        i = np.argmax(np.abs(r[mid]))
        print(f"z={z:5.0f} cutoff {lc:5.0f}: residual x1500-7000 p-p {np.ptp(r[mid]):5.2f} mm full ({np.ptp(r[mid])/30:.3f} model), rms {r[mid].std():.2f}; "
              f"dominant wavelength {1/fr[k]:4.0f} mm; max at x={x[mid][i]:.0f}")
        out[(z, lc)] = r
    dev = y - R["ya"]
    j = np.nanargmax(np.abs(dev))
    print(f"        loft minus analytic section: max |dev| {np.nanmax(np.abs(dev)):.1f} mm at x={x[j]:.0f};  x1500-7000: p-p {np.nanmax(dev[mid])-np.nanmin(dev[mid]):.1f}")
    # deviation at stations vs between stations
    at = np.array([np.interp(s, x, dev) for s in xs_st if x[0] < s < x[-1]])
    midp = 0.5 * (xs_st[1:] + xs_st[:-1]); bt = np.array([np.interp(s, x, dev) for s in midp if x[0] < s < x[-1]])
    print(f"        |dev| at stations: median {np.nanmedian(np.abs(at)):.2f}, max {np.nanmax(np.abs(at)):.2f};  midway between stations: median {np.nanmedian(np.abs(bt)):.2f}, max {np.nanmax(np.abs(bt)):.2f}")
np.save(OUT + "/ripple_res.npy", out, allow_pickle=True)
