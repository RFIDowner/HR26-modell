import sys, json
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/11dad074fa1abe1e/d28ff77b-a16b-454a-a3fa-4f83bd19bf4c/scratchpad/undervann/py")
import numpy as np
from PIL import Image, ImageDraw
import uw
D = uw.SNAP + "/photo/"
im = Image.fromarray(uw.photo("IMG_9388")); d = ImageDraw.Draw(im)
m = json.load(open(D + "m9388.json"))
for v, ob, ib in m["left"]: d.point((ob, v), fill=(0, 255, 0)); d.point((ib, v), fill=(255, 255, 0))
for v, ob, ib in m["right"]: d.point((ob, v), fill=(0, 255, 0)); d.point((ib, v), fill=(255, 255, 0))
for u, v in m["bt_top"]: d.point((u, v), fill=(255, 0, 255))
for v, a, b in m["stem"]: d.point((0.5 * (a + b), v), fill=(0, 255, 255))
bt = json.load(open(D + "bt9388.json"))["pts"]
for u, v in bt: d.ellipse([u - 3, v - 3, u + 3, v + 3], outline=(255, 128, 0))
im.crop((100, 0, 1300, 1100)).save(uw.OUT + "/view/tr9388.png")
im = Image.fromarray(uw.photo("IMG_9391")); d = ImageDraw.Draw(im)
m = json.load(open(D + "m9391.json"))
for r in m["strake"]: d.point((r[0], r[3]), fill=(0, 255, 0))
for r in m["boottop"]: d.point((r[0], r[1]), fill=(255, 0, 255))
for v, u in m["sil_right"]: d.point((u, v), fill=(0, 255, 0))
s = json.load(open(D + "m9391_strake.json"))["strake"]
for r in s: d.point((r[0], r[3]), fill=(255, 255, 0))
im.crop((0, 0, 1500, 1100)).save(uw.OUT + "/view/tr9391.png")
