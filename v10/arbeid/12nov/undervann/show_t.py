"""show_t.py NAME tracefile x0 y0 x1 y1 scale out  -> overlay of all [v,u] / [u,v] lists in the trace file"""
import sys, json
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/11dad074fa1abe1e/d28ff77b-a16b-454a-a3fa-4f83bd19bf4c/scratchpad/undervann/py")
import numpy as np
from PIL import Image, ImageDraw
import uw
name, tf = sys.argv[1], sys.argv[2]
x0, y0, x1, y1 = map(int, sys.argv[3:7]); sc = float(sys.argv[7]); outn = sys.argv[8]
t = json.load(open(tf))
im = Image.fromarray(uw.photo(name)).crop((x0, y0, x1, y1))
im = im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS)
d = ImageDraw.Draw(im)
cols = [(0, 255, 0), (255, 0, 255), (255, 255, 0), (0, 255, 255), (255, 128, 0), (255, 255, 255), (0, 128, 255), (255, 0, 0)]
i = 0
for k, v in t.items():
    if not isinstance(v, list) or not v or not isinstance(v[0], list):
        continue
    c = cols[i % len(cols)]; i += 1
    uv = k.startswith("uv_")
    for p in v:
        if uv:
            u, vv = p[0], p[1]
        else:
            vv, u = p[0], p[1]
        X, Y = (u - x0) * sc, (vv - y0) * sc
        d.ellipse([X - 1.5, Y - 1.5, X + 1.5, Y + 1.5], fill=c)
    d.text((5, 5 + 14 * i), k, fill=c)
im.save(uw.OUT + "/view/" + outn)
print(im.size)
