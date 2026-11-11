import sys
from PIL import Image, ImageOps, ImageDraw, ImageFont
name, x0, y0, x1, y1, k = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), float(sys.argv[6])
step = int(sys.argv[7]) if len(sys.argv) > 7 else 50
im = ImageOps.exif_transpose(Image.open(f"C:/Users/stig/Documents/Seilbåt/{name}.jpeg")).convert("RGB")
c = im.crop((x0, y0, x1, y1)).resize((round((x1 - x0) * k), round((y1 - y0) * k)), Image.LANCZOS)
d = ImageDraw.Draw(c)
f = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 13)
for gx in range((x0 // step + 1) * step, x1, step):
    X = (gx - x0) * k
    d.line([(X, 0), (X, c.size[1])], fill=(255, 0, 255) if gx % (step * 2) == 0 else (0, 255, 255), width=1)
    d.text((X + 2, 2), str(gx), fill=(255, 255, 0), font=f)
for gy in range((y0 // step + 1) * step, y1, step):
    Y = (gy - y0) * k
    d.line([(0, Y), (c.size[0], Y)], fill=(255, 0, 255) if gy % (step * 2) == 0 else (0, 255, 255), width=1)
    d.text((2, Y + 2), str(gy), fill=(255, 255, 0), font=f)
out = f"g_{name}_{x0}_{y0}.png"
c.save(out)
print(out, c.size)
