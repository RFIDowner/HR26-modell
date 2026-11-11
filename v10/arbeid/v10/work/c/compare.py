"""Foer/etter-bilder av dekket: samme kamera og utsnitt for to STL-er i
baatkoordinater (build_hull_only), satt sammen over hverandre.

python compare.py before.stl after.stl outprefix [view ...]
"""
import sys
from PIL import Image, ImageDraw
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/work/c")
from rend import render

VIEWS = {
    # navn: (bredde, az, el, roi x0,x1,y0,y1,z0,z1, tekst)
    "q34aft": (1500, 35, 32, (1500, 8000, -1500, 1500, 600, 1900), "3/4 fra akter og over (som IMG_9304)"),
    "topaft": (1500, 8, 50, (1500, 8000, -1500, 1500, 600, 1900), "fra akter, hoyt (som IMG_9372)"),
    "side": (1500, 90, 2, (-50, 8000, -1500, 1500, 700, 1900), "fra siden"),
    "bow": (1300, 155, 22, (-50, 1700, -900, 900, 700, 1450), "baugen"),
    "front": (1400, 205, 22, (1500, 3600, -1400, 1400, 900, 1550), "ruffens front"),
    "hood": (1400, 40, 18, (4600, 7000, -1400, 1400, 950, 1850), "sprayhood, karm og vinsjer"),
    "stern": (1400, 25, 30, (6400, 8000, -1300, 1300, 700, 1300), "akterdekk og klamp"),
}


def compare(before, after, prefix, views):
    for v in views:
        W, az, el, roi, text = VIEWS[v]
        a = render(prefix + f"_{v}_foer.png", W, az, el, roi, [before + ":model"], label="FOER: " + text)
        b = render(prefix + f"_{v}_etter.png", W, az, el, roi, [after + ":model"], label="ETTER (V10): " + text)
        out = Image.new("RGB", (max(a.width, b.width), a.height + b.height + 6), (255, 255, 255))
        out.paste(a, (0, 0))
        out.paste(b, (0, a.height + 6))
        if out.width > 1600:
            s = 1600 / out.width
            out = out.resize((1600, int(out.height * s)), Image.LANCZOS)
        out.save(prefix + f"_{v}.png")
        print("->", prefix + f"_{v}.png", out.size)


if __name__ == "__main__":
    compare(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:] or list(VIEWS))
