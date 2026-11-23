import sys
from PIL import Image
src, out, x0, y0, x1, y1 = sys.argv[1], sys.argv[2], *map(float, sys.argv[3:7])
im = Image.open(src)
print(im.size)
W, H = im.size
box = (int(x0*W), int(y0*H), int(x1*W), int(y1*H))
c = im.crop(box)
s = min(1600 / c.size[0], 1200 / c.size[1])
c = c.resize((int(c.size[0]*s), int(c.size[1]*s)), Image.LANCZOS)
c.save(out)
print(out, c.size)
