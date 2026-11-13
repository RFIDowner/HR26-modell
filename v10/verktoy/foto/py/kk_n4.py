"""kk_: nye (4) (babord side paa land) - modellen rendret med hovedkameraet
(fprof:pin_Nc_f850) ved siden av bildet, utsnitt over listen akter.
Ut (scratchpad): kk_n4_render.png, kk_n4_pair.png, kk_n4_xyz.npz"""
import sys
import numpy as np
from PIL import Image
import common as c
import geo9374 as G
G.use_model(None)
import n4_ovl as O
import kk_lib as L

SP = sys.argv[1]
cam, d = O.load("fprof:pin_Nc_f850")
V, F = L.model_mesh()
S = 2.0
img, XYZ = L.render(cam, V, F, scale=S)
Image.fromarray(img).save(SP + "/kk_n4_render.png")
np.savez_compressed(SP + "/kk_n4_xyz.npz", XYZ=XYZ.astype(np.float32), S=S)
ph = Image.open(O.IMG).convert("RGB")
ph = ph.resize((int(ph.width * S), int(ph.height * S)), Image.LANCZOS)
box = [int(560 * S), int(280 * S), int(1030 * S), int(440 * S)]
a = ph.crop(box)
b = Image.fromarray(img).crop(box)
pair = Image.new("RGB", (a.width, a.height * 2 + 6), (0, 0, 0))
pair.paste(a, (0, 0))
pair.paste(b, (0, a.height + 6))
pair.save(SP + "/kk_n4_pair.png")
print("cam C", np.round(cam.C), "f", cam.f)
