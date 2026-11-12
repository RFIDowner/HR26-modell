import sys
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/11dad074fa1abe1e/d28ff77b-a16b-454a-a3fa-4f83bd19bf4c/scratchpad/undervann/py")
import numpy as np
from PIL import Image
import uw
name, x0, y0, x1, y1, sc = sys.argv[1], *map(int, sys.argv[2:6]), float(sys.argv[6])
a = uw.photo(name).astype(float)
R, G, B = a[..., 0], a[..., 1], a[..., 2]
red = R - np.maximum(G, B)
chroma = np.clip(red / 120.0, 0, 1)
L = a.mean(2)
# false colour: redness in red channel, luminance in green/blue
out = np.dstack([chroma * 255, L * 0.6, L * 0.6]).astype(np.uint8)[y0:y1, x0:x1]
im = Image.fromarray(out)
im = im.resize((int(im.width * sc), int(im.height * sc)), Image.NEAREST)
im.save(uw.OUT + f"/view/red_{name}.png")
print(im.size)
