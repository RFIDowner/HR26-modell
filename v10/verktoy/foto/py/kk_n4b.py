"""kk_: nye (4) - renderkanter (roedt) og modellkurver over bildet, utsnitt akter."""
import sys
import numpy as np
from PIL import Image, ImageDraw
import common as c
import geo9374 as G
G.use_model(None)
import n4_ovl as O
import kk_lib as L
import kk_edges as E
from hr26 import deckhouse as D
P, C = c.P, c.C
SP = sys.argv[1]
cam, d = O.load("fprof:pin_Nc_f850")
S = 3.0
V, F = L.model_mesh()
img, XYZ = L.render(cam, V, F, scale=S)
np.savez_compressed(SP + "/kk_n4_xyz3.npz", XYZ=XYZ.astype(np.float32))
Image.fromarray(img).save(SP + "/kk_n4_render3.png")
ph = Image.open(O.IMG).convert("RGB")
ph = np.asarray(ph.resize((int(ph.width * S), int(ph.height * S)), Image.LANCZOS))
m = E.edge_mask(img, XYZ)
ov = Image.fromarray(E.overlay(ph, m, alpha=0.6))
dr = ImageDraw.Draw(ov)


def curve(X, col, w=2):
    u, v, z = cam.project(np.asarray(X))
    dr.line(list(zip(u * S, v * S)), fill=col, width=w)


xs = np.linspace(3000, 7950, 300)
curve([[x, -C.deck_half_breadth(x), C.sheer_z(x)] for x in xs], (0, 200, 255))
xc = np.linspace(P.COCKPIT_X0 - P.COAMING_FWD + P.COAMING_RAD, P.COAMING_X1, 100)
curve([[x, -D.coaming_half_width(x), D.coaming_top_z(x)] for x in xc], (255, 230, 0))
box = [int(560 * S), int(290 * S), int(1030 * S), int(440 * S)]
ov.crop(box).save(SP + "/kk_n4_edges.png")
Image.fromarray(ph).crop(box).save(SP + "/kk_n4_photo3.png")
Image.fromarray(img).crop(box).save(SP + "/kk_n4_rcrop3.png")
