import sys
sys.path.insert(0, "C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/robot/edges")
from PIL import Image, ImageDraw
from lib import OUT, font
W = OUT + "/work"
def lab(img, t, xy=(8, 6), size=17, col=(0, 0, 0)):
    dr = ImageDraw.Draw(img); f = font(size)
    bb = dr.textbbox(xy, t, font=f); dr.rectangle([bb[0]-4, bb[1]-3, bb[2]+4, bb[3]+3], fill=(255, 255, 255))
    dr.text(xy, t, font=f, fill=col); return img
def sheet(rows, title, fn, cw=790, ch=420):
    H = 50 + len(rows) * (ch + 34)
    out = Image.new("RGB", (2 * cw + 12, H), (255, 255, 255)); dr = ImageDraw.Draw(out)
    dr.text((8, 10), title, font=font(19), fill=(0, 0, 0))
    y = 46
    for (rt, a, at, b, bt) in rows:
        dr.text((8, y + 4), rt, font=font(16), fill=(50, 50, 50))
        A = Image.open(a); B = Image.open(b) if b else Image.new("RGB", (cw, ch), (255, 255, 255))
        lab(A, at, col=(170, 0, 0)); 
        if b: lab(B, bt, col=(0, 50, 190))
        out.paste(A, (0, y + 28)); out.paste(B, (cw + 12, y + 28))
        dr.rectangle([0, y + 28, cw - 1, y + 28 + ch - 1], outline=(190, 190, 190))
        dr.rectangle([cw + 12, y + 28, 2 * cw + 11, y + 28 + ch - 1], outline=(190, 190, 190))
        y += ch + 34
    out.save(fn); print(fn, out.size)
sheet([
 ("Bow, from starboard bow (same camera)", f"{W}/cu2_bow_ours.png", "ours: roller block 520x170x140 + its lower end sticks out of the stem; square strake", f"{W}/cu2_bow_bambu.png", "Bambu: rounded rim wraps the stem, toe rail, no blocks"),
 ("Midships deck edge, x 2500-4100, low side view", f"{W}/cu2_deck_ours.png", "ours: sharp 75 deg deck edge, square strake, faceted coachroof wall", f"{W}/cu2_deck_bambu.png", "Bambu: toe-rail bead, rounded strake, framed window"),
 ("Coachroof front", f"{W}/cu2_front_ours.png", "ours: vertical wall (45 deg cut silently failed), R=0 top edge", f"{W}/cu2_front_bambu.png", "Bambu: steep front, top edge R~25 mm, sides lean in 12 deg"),
 ("Stern, from aft starboard", f"{W}/cu2_stern_ours.png", "ours: R=0 transom/deck edges, brick cleats, strake knuckle", f"{W}/cu2_stern_bambu.png", "Bambu: rounded transom corners, continuous rim"),
], "Flat-shaded close-ups like Bambu Studio: ours (left, 01_skrog.stl) vs Bambu (right, scaled x0.3708)", OUT + "/edges_closeups.png")
sheet([
 ("Strake at the bow (x=200) and anchor-roller block under the stem", f"{W}/cu3_strake_bow_ours.png", "ours: strake ends in a flat 95x55 face; block corner pokes out below", f"{W}/cu3_strake_bow_bambu.png", "Bambu: bead runs round the stem"),
 ("Strake round the transom corner (x 7635-7841)", f"{W}/cu3_strake_stern_ours.png", "ours: 3 ruled facets with kinks 16/10/26 deg = a 'knuckle'", f"{W}/cu3_strake_stern_bambu.png", "Bambu: continuous rounded bead"),
 ("Winch at x=5900 inside the sprayhood", f"{W}/cu2_winch_ours.png", "ours: D300 winch drum cut by the hood flank (looks like a funnel)", f"{W}/cu2_winch_bambu.png", "Bambu: winches are small separate drums, not merged into the hood"),
], "Boxy details: ours (left) vs Bambu (right)", OUT + "/edges_details.png")
