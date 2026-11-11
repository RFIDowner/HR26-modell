import sys, math
from PIL import Image, ImageDraw
src = "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/wt/deck/docs/images/overlegg-plan.jpg"
PX = 3.27
im = Image.open(src).convert("RGB")
# senterlinje: finn raden midt mellom ytterkantene
x0, x1, y0, y1, zoom, out = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]), sys.argv[6]
CROW = float(sys.argv[7]) if len(sys.argv) > 7 else 490.0
def X(xf): return 2508 - xf / 3.257
def Y(yf): return CROW - yf / 3.257
box = (int(X(x1)), int(Y(y1)), int(X(x0)), int(Y(y0)))
c = im.crop(box).resize((int((box[2]-box[0])*zoom), int((box[3]-box[1])*zoom)), Image.NEAREST)
d = ImageDraw.Draw(c)
xs = math.ceil(x0/100)*100
while xs <= x1:
    u = (X(xs)-box[0])*zoom
    d.line([(u,0),(u,c.height)], fill=(0,160,255) if xs % 500 else (0,0,255), width=1)
    d.text((u-14, 2), f"{xs:.0f}", fill=(0,0,255)); xs += 100
ys = math.ceil(y0/100)*100
while ys <= y1:
    v = (Y(ys)-box[1])*zoom
    d.line([(0,v),(c.width,v)], fill=(0,200,0) if ys % 500 else (0,120,0), width=1)
    d.text((2, v+1), f"{ys:.0f}", fill=(0,120,0)); ys += 100
c.save(out); print(out, c.size)
