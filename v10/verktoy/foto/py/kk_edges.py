"""kk_: kanter fra en render (graatone-gradient + silhuett + dybdesprang)
tegnet over bildet. Brukes av kk_n4/kk_n6-analysene."""
import numpy as np
from scipy import ndimage as ndi


def edge_mask(img, XYZ, thr=18.0, dthr=0.04):
    g = img.astype(float).mean(-1)
    gx = ndi.sobel(g, 1)
    gy = ndi.sobel(g, 0)
    m = np.hypot(gx, gy) > thr * 4
    bg = ~np.isfinite(XYZ[..., 0])
    sil = bg ^ ndi.binary_erosion(bg)
    d = np.where(bg, np.nan, np.linalg.norm(XYZ, axis=-1))
    dz = np.zeros_like(g, bool)
    with np.errstate(invalid="ignore"):
        for ax in (0, 1):
            dd = np.abs(np.diff(d, axis=ax))
            rel = dd / np.nanmax([np.nanmean(d), 1.0])
            j = np.zeros_like(g, bool)
            if ax == 0:
                j[1:, :] = rel > dthr
            else:
                j[:, 1:] = rel > dthr
            dz |= j
    return m | sil | dz


def overlay(photo, mask, col=(255, 0, 0), alpha=0.85):
    out = photo.astype(float).copy()
    out[mask] = (1 - alpha) * out[mask] + alpha * np.array(col, float)
    return out.astype(np.uint8)
