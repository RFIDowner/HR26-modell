import sys
from PIL import Image, ImageDraw, ImageFont
OUT = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/surface"
rows = [("ours", "01_skrog.stl as shipped (128k tri incl. deck; hull 16k)"),
        ("loft_shipped_tol", "bare loft, shipped tolerance 0.018 mm (22k tri)"),
        ("loft_exact", "bare loft, tolerance 0.002 mm (909k tri) = the true surface"),
        ("bambu", "Bambu AI model, rails/mast cropped (224k tri)")]
cols = ["flat (as Bambu Studio shows STL)", "smooth vertex normals", "reflection lines (zebra)"]
pw, ph = 520, 330
try:
    font = ImageFont.truetype("arial.ttf", 15); fs = ImageFont.truetype("arial.ttf", 13)
except Exception:
    font = fs = ImageFont.load_default()
sheet = Image.new("RGB", (pw * 3 + 20, 34 + len(rows) * (ph + 26)), (252, 252, 251))
d = ImageDraw.Draw(sheet)
for j, c in enumerate(cols):
    d.text((10 + j * pw + 8, 8), c, fill=(11, 11, 11), font=font)
for i, (nm, lab) in enumerate(rows):
    y0 = 34 + i * (ph + 26)
    d.text((18, y0 + 2), lab, fill=(82, 81, 78), font=fs)
    for j, m in enumerate(("flat", "smooth", "zebra")):
        im = Image.open(f"{OUT}/panel_{nm}_{m}.png")
        im.thumbnail((pw - 8, ph - 4), Image.LANCZOS)
        sheet.paste(im, (10 + j * pw + 4, y0 + 22))
sheet.save(f"{OUT}/fig2_render_sheet.png")
print(sheet.size)
