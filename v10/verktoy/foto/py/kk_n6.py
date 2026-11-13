"""kk_: nye (6) (styrbord laaring, lavt) - modellen rendret med kamera
pin_keel (eller argv[2]), kanter og kurver over bildet. Ut i scratchpad."""
import sys
import json
import numpy as np
from PIL import Image, ImageDraw, ImageOps
import common as c
import geo9374 as G
G.use_model(None)
import n6_cam as K
import kk_lib as L
import kk_edges as E
from hr26 import deckhouse as D
P, C = c.P, c.C
SP = sys.argv[1]
MODE = sys.argv[2] if len(sys.argv) > 2 else "pin_keel"
J = json.load(open(c.W + "/out/n6_cam.json"))
d = J["modes"][MODE]
cam = K.make_cam(np.asarray(d["q"], float), d["cfg"]["mode"])
S = 2.0
V, F = L.model_mesh()
img, XYZ = L.render(cam, V, F, scale=S)
np.savez_compressed(SP + "/kk_n6_xyz.npz", XYZ=XYZ.astype(np.float32))
ph0 = Image.open(c.FOTO + "/nye (6).jpeg").convert("RGB")
ph = np.asarray(ph0.resize((int(ph0.width * S), int(ph0.height * S)), Image.LANCZOS))
m = E.edge_mask(img, XYZ)
ov = Image.fromarray(E.overlay(ph, m, alpha=0.6))
dr = ImageDraw.Draw(ov)


def curve(X, col, w=2):
    u, v, z = cam.project(np.asarray(X))
    dr.line(list(zip(u * S, v * S)), fill=col, width=w)


xs = np.linspace(4000, 7950, 300)
curve([[x, C.deck_half_breadth(x), C.sheer_z(x)] for x in xs], (0, 200, 255))
xc = np.linspace(P.COCKPIT_X0 - P.COAMING_FWD + P.COAMING_RAD, P.COAMING_X1, 100)
curve([[x, D.coaming_half_width(x), D.coaming_top_z(x)] for x in xc], (255, 230, 0))
box = [int(150 * S), int(560 * S), int(1130 * S), int(830 * S)]
ov.crop(box).save(SP + "/kk_n6_edges.png")
Image.fromarray(img).crop(box).save(SP + "/kk_n6_rcrop.png")
print(np.round(cam.C), cam.f)
