"""kk_: loddrette lysprofiler i bilde og render (nye (6)) - kanter mellom listen og toppen."""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
import common as c
SP = sys.argv[1]
ph = np.asarray(Image.open(c.FOTO + "/nye (6).jpeg").convert("L")).astype(float)
rd = np.asarray(Image.open(SP + "/kk_n6_render_full.png").convert("L")).astype(float) if len(sys.argv) > 9 else None
X = np.load(SP + "/kk_n6_xyz.npz")["XYZ"]
S = 2.0
for u in [int(a) for a in sys.argv[2:]]:
    col = ndi.gaussian_filter1d(ph[:, u - 1:u + 2].mean(1), 1.0)
    g = np.gradient(col)
    vs = np.arange(600, 800)
    ext = [(v, round(g[v], 1)) for v in vs if abs(g[v]) > 3 and abs(g[v]) >= abs(g[v - 1]) and abs(g[v]) >= abs(g[v + 1])]
    # modellens punkt i hver rad
    uu = int(u * S)
    mz = [(v, X[int(v * S), uu].round(0).tolist()) for v in range(640, 800, 10) if np.isfinite(X[int(v * S), uu, 0])]
    print("u", u, "photo edges", ext)
    print("   model", mz)
