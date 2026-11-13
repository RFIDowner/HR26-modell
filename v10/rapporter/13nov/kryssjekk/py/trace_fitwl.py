"""Seed = waterline (z -23) of the joint-fit hull; search the 448-5 plan for the
dash-dot line along the whole length (+-50 mm), both sides."""
import sys, json, importlib
sys.path.insert(0, sys.argv[1])
import numpy as np
from PIL import Image
from hr26 import params as P, curves as C
q = json.load(open(sys.argv[2]))["params"]
P.SECTION_DEADRISE = [(0.00, 45.0), (0.127, 15.0), (0.20, 4.0), (0.30, q["dr30"]), (0.45, q["dr45"]), (0.60, q["dr60"]), (0.75, q["dr75"]), (0.90, q["dr90"]), (1.00, 3.0)]
P.SECTION_N = [(0.00, 2.4), (0.15, 3.1), (0.30, q["n30"]), (0.45, q["n45"]), (0.80, q["n80"]), (1.00, 4.2)]
d = q["dw_h_mid"]; w = q["dw_w_mid"]
P.DEADWOOD_H = [(2900.0, 0.0), (3600.0, d), (5900.0, d), (6800.0, max(d, 100.0)), (7400.0, 170.0), (7800.0, 210.0), (8000.0, 210.0)]
P.DEADWOOD_W = [(3600.0, w), (5900.0, w), (6800.0, 120.0)]
C = importlib.reload(sys.modules["hr26.curves"])
S=4.2591; XB=2240.1; YC=1333.2
im=np.asarray(Image.open(r"C:/Users/stig/Documents/Seilbåt/Hallberg-Rassy-kilder/HR26interior448-5.jpeg").convert("L"),dtype=np.uint8)
def hb(x,z):
    p=C._section_geom(float(x))["pts"]
    for i in range(len(p)-1):
        if (p[i,1]-z)*(p[i+1,1]-z)<=0 and p[i+1,1]!=p[i,1]:
            t=(z-p[i,1])/(p[i+1,1]-p[i,1]); return float(p[i,0]+t*(p[i+1,0]-p[i,0]))
    return float("nan")
rows=[]
for xb in range(1250,7751,250):
    found={}
    for side,sgn in (("stb",-1),("port",1)):
        ys=[]
        for xmm in np.arange(xb-100,xb+101,10):
            y0=hb(xmm,-23.0)
            if not np.isfinite(y0) or xmm>C.transom_x(-23.0): continue
            px=int(round(XB-xmm/S)); pc=YC-sgn*y0/S; lo,hi=int(pc-12),int(pc+12)
            col=im[lo:hi+1,px-1:px+2].astype(float).mean(axis=1); j=int(np.argmin(col)); med=np.median(col)
            if col[j]<150 and med-col[j]>45:
                ys.append(abs((YC-(lo+j))*S)-y0)
        found[side]=(len(ys),round(float(np.median(ys))) if ys else None)
    rows.append((xb,round(hb(xb,-23.0)) if xb<C.transom_x(-23.0) else None,found))
for r in rows: print(r)
