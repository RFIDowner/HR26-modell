import sys
import numpy as np
from PIL import Image
im = np.asarray(Image.open(sys.argv[1]).convert('L')).astype(float)
H, W = im.shape
y0, y1, x0, x1 = int(H*0.53), int(H*0.97), int(W*0.03), int(W*0.93)
reg = im[y0:y1, x0:x1] < 120
# radene med mye mork strek er skrogomrisset; finn senterlinjeraden som raden der baugspissen stikker lengst
cols = np.where(reg.any(axis=0))[0]
rows_any = reg.any(axis=1)
# baug: lengst til hoyre mork piksel per rad
right = np.array([np.where(r)[0].max() if r.any() else -1 for r in reg])
left = np.array([np.where(r)[0].min() if r.any() else 10**9 for r in reg])
cy = int(np.argmax(right)); xb = right[cy]
# akterspeil: minste venstre x i radene naer senterlinjen (+-15 % av hoyden)
band = slice(max(0, cy-60), cy+60)
xa = left[band].min()
loa_px = xb - xa
# bredde: ved kolonnen midt mellom, finn ytterste morke piksler over/under cy innenfor omrisset
def extent(col):
    c = reg[:, col]; ys = np.where(c)[0]
    return ys.min(), ys.max()
best = None
for col in range(xa + int(0.35*loa_px), xa + int(0.75*loa_px), 3):
    a, b = extent(col)
    if best is None or (b - a) > best[1] - best[0]: best = (a, b, col)
beam_px = best[1] - best[0]
s = 7950.0 / loa_px
print(f'bilde {W}x{H}; LOA {loa_px} px -> {s:.2f} mm/px; bredde {beam_px} px -> {beam_px*s:.0f} mm (oppgitt 2680)')
# skott: kolonner der en lang loddrett strek dekker mye av skrogbredden
inside = reg[best[0]+15:best[1]-15, :]
score = inside.sum(axis=0) / max(1, inside.shape[0])
peaks = [c for c in range(xa+10, xb-10) if score[c] > 0.55 and score[c] >= score[c-2:c+3].max()]
merged = []
for c in peaks:
    if not merged or c - merged[-1][-1] > 6: merged.append([c])
    else: merged[-1].append(c)
for g in merged:
    c = int(np.mean(g)); print(f'  lang loddrett strek ved x = {7950 - (c - xa)*s:5.0f} mm fra baugen? (fra akter: {(c - xa)*s:5.0f})  dekning {score[c]:.2f}')
