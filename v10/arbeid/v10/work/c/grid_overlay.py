import sys
from PIL import Image, ImageDraw
src = "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/deck/docs/images/overlegg-profil.jpg"
PX = 3.27
def X(xf): return 2510 - xf / PX
def R(z): return 424 - (z - 793) / PX
x0, x1, z0, z1, zoom, out = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]), sys.argv[6]
dx = float(sys.argv[7]) if len(sys.argv) > 7 else 100
dz = float(sys.argv[8]) if len(sys.argv) > 8 else 50
im = Image.open(src).convert("RGB")
box = (int(X(x1)), int(R(z1)), int(X(x0)), int(R(z0)))
c = im.crop(box).resize((int((box[2]-box[0])*zoom), int((box[3]-box[1])*zoom)), Image.NEAREST)
d = ImageDraw.Draw(c)
import math
xs = math.ceil(x0/dx)*dx
while xs <= x1:
    u = (X(xs)-box[0])*zoom
    d.line([(u,0),(u,c.height)], fill=(0,160,255) if xs % (5*dx) else (0,0,255), width=1)
    d.text((u-14, 2), f"{xs:.0f}", fill=(0,0,255)); d.text((u-14, c.height-12), f"{xs:.0f}", fill=(0,0,255))
    xs += dx
zs = math.ceil(z0/dz)*dz
while zs <= z1:
    v = (R(zs)-box[1])*zoom
    d.line([(0,v),(c.width,v)], fill=(0,200,0), width=1)
    d.text((2, v+1), f"{zs:.0f}", fill=(0,120,0))
    zs += dz
c.save(out); print(out, c.size)
