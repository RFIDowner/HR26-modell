import sys
import numpy as np
from PIL import Image, ImageOps
from scipy import ndimage as ndi
name = sys.argv[1]
im = ImageOps.exif_transpose(Image.open(f"C:/Users/stig/Documents/Seilbåt/{name}.jpeg")).convert("RGB")
a = np.asarray(im).astype(float)
r, g, b = a[..., 0], a[..., 1], a[..., 2]
red = (r > 110) & (r > 1.6 * g) & (r > 1.5 * b)
red = ndi.binary_opening(red, iterations=2)
lab, n = ndi.label(red)
sizes = ndi.sum(red, lab, range(1, n + 1))
keep = np.argsort(sizes)[::-1][:3] + 1
big = np.isin(lab, keep[sizes[keep - 1] > 0.02 * sizes.max()])
big = ndi.binary_closing(big, iterations=3)
big = ndi.binary_fill_holes(big)
np.save(f"red_{name}.npy", big)
out = (np.dstack([big * 255, a[..., 1] * 0.5, a[..., 2] * 0.5])).astype(np.uint8)
Image.fromarray(out).resize((im.size[0] // 3, im.size[1] // 3)).save(f"red_{name}.png")
ys, xs = np.nonzero(big)
print(name, "red px", big.sum(), "bbox", xs.min(), xs.max(), ys.min(), ys.max())
