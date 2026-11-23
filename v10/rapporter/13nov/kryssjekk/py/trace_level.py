"""Trace the 448-5 plan dash-dot line along the whole boat, seeded by the HEAD
hull's half-breadth at z=-300 (search +-45 mm), then report the height z at
which each stage's hull has that half-breadth."""
import sys, json
sys.path.insert(0, sys.argv[1])          # HEAD stage for the seed
import numpy as np
from PIL import Image
from hr26 import curves as C
S=4.2591; XB=2240.1; YC=1333.2
im=np.asarray(Image.open(r"C:/Users/stig/Documents/Seilbåt/Hallberg-Rassy-kilder/HR26interior448-5.jpeg").convert("L"),dtype=np.uint8)
def hb(x,z):
    p=C._section_geom(float(x))["pts"]
    for i in range(len(p)-1):
        if (p[i,1]-z)*(p[i+1,1]-z)<=0 and p[i+1,1]!=p[i,1]:
            t=(z-p[i,1])/(p[i+1,1]-p[i,1]); return float(p[i,0]+t*(p[i+1,0]-p[i,0]))
    return float("nan")
pts={"stb":[],"port":[]}
for xmm in np.arange(1200,7000,10):
    y0=hb(xmm,-300.0)
    if not np.isfinite(y0): continue
    px=int(round(XB-xmm/S))
    for side,sgn in (("stb",-1),("port",1)):
        pc=YC-sgn*y0/S; lo,hi=int(pc-11),int(pc+11)
        col=im[lo:hi+1,px-1:px+2].astype(float).mean(axis=1)
        j=int(np.argmin(col)); med=np.median(col)
        if col[j]<150 and med-col[j]>45:
            w=np.clip(med-col[max(j-2,0):j+3],0,None)
            py=lo+max(j-2,0)+float((w*np.arange(len(w))).sum()/w.sum())
            pts[side].append((float(xmm),abs(float((YC-py)*S)),float(y0)))
json.dump(pts,open(sys.argv[2],"w"))
for side in pts:
    a=np.array(pts[side]); print(side,len(a))
    for xb in range(1250,7001,250):
        m=(a[:,0]>=xb-100)&(a[:,0]<xb+100)
        if m.sum()>=2: print("  x %4d: |y| %4.0f (n %2d, sd %3.0f)  HEAD hb(-300) %4.0f"%(xb,np.median(a[m,1]),m.sum(),np.std(a[m,1]),np.median(a[m,2])))
