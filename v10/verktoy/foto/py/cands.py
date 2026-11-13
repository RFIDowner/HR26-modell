"""Candidate canoe bodies: profile (CANOE_BOTTOM_HIDDEN) and section (SECTION_DEADRISE, SECTION_N) variants."""
import sys; sys.path.insert(0, '.')
import numpy as np
import common as c

BASE = dict(CANOE_BOTTOM_HIDDEN=list(c.P.CANOE_BOTTOM_HIDDEN), SECTION_DEADRISE=list(c.P.SECTION_DEADRISE),
            SECTION_N=list(c.P.SECTION_N), SECTION_FLARE=list(c.P.SECTION_FLARE))

def e_mapped_aft():
    a = c.eline("hull_aft_bottom")
    a = a[a[:, 0] > 5950]
    a = a[np.argsort(a[:, 0])]
    return a[:, 0], (a[:, 1] - 25.5) / 0.968

def hidden_aft(mode="E", z_keel=-470.0, x_deep=4400.0):
    """Hidden canoe body: under the keel a fair belly, aft of the keel the drawings' flat run.
    mode 'E' = Enderlein mapped into the model frame, 'B' = brochure flat -449, 'M' = mean of both."""
    xe, ze = e_mapped_aft()
    xs = np.array([6000., 6250, 6500, 6750, 7000, 7250, 7500, 7650, 7800, 7950])
    zE = np.interp(xs, xe, ze, right=ze[-1] + (ze[-1] - ze[-40]) / (xe[-1] - xe[-40]) * 0)
    # beyond the transom foot (7778) continue the last slope (loft runs past the transom and is cut)
    sl = (ze[-1] - ze[-60]) / (xe[-1] - xe[-60])
    zE = np.where(xs > xe[-1], ze[-1] + sl * (xs - xe[-1]), zE)
    zB = np.full(len(xs), -449.0)
    zz = {"E": zE, "B": zB, "M": 0.5 * (zE + zB)}[mode]
    fwd = [(3250.0, -455.3), (3500.0, -470.0), (3750.0, z_keel + 0.0), (4000.0, z_keel), (4250.0, z_keel),
           (4500.0, z_keel), (4590.0, z_keel), (4750.0, z_keel), (5000.0, z_keel + 2), (5250.0, z_keel + 5),
           (5500.0, 0.5 * (z_keel + 5 + zz[0])), (5750.0, 0.25 * (z_keel + 5) + 0.75 * zz[0])]
    return fwd + [(float(x), float(z)) for x, z in zip(xs, zz)]

def apply(**over):
    kw = dict(BASE); kw.update(over)
    return c.reload_model(**kw)
