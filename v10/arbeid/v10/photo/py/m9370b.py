import sys, json, numpy as np
sys.path.insert(0, r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/photo/py")
from track import track
from PIL import Image
D = r"C:/Users/stig/AppData/Local/Temp/claude/12681ed4fad82730/bbd7b4f2-5285-465a-8464-b20ca4b41c67/scratchpad/v10/photo"
a = np.asarray(Image.open(f"{D}/up/IMG_9370.png").convert("RGB")).astype(float)
L = a.mean(2)
S = track(L, 650, 1254, 152, 990, win=3, maxjump=1.2)
print(len(S), S[0], S[-1])
d = np.diff(S[:, 3]); print("max jump", abs(d).max(), "gaps", np.nonzero(np.diff(S[:, 0]) > 1)[0][:20])
for u in (153, 160, 170, 180, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 925, 950, 970, 980, 985, 988):
    i = np.argmin(abs(S[:, 0] - u)); r = S[i]
    print("u %4d top %.1f bot %.1f ctr %.2f thick %.1f" % (r[0], r[1], r[2], r[3], r[2] - r[1]))
json.dump({"strake": S.tolist()}, open(f"{D}/m9370_strake.json", "w"))
