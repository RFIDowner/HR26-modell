"""Trace the dash-dot line inside the saloon settees in the 448-5 plan (both sides).
Seed: hand reading y(x) ~ 630@3000, 700@3750, 790@4500, 840@5000, 860@5250 (mm)."""
import json, sys
import numpy as np
from PIL import Image
S=4.2591; XB=2240.1; YC=1333.2
im=np.asarray(Image.open(r"C:/Users/stig/Documents/Seilbåt/Hallberg-Rassy-kilder/HR26interior448-5.jpeg").convert("L"),dtype=np.uint8)
seed_x=np.array([3000,3400,3750,4000,4500,5000,5250,5450.]); seed_y=np.array([630,680,700,740,790,840,860,870.])
out={}
for side,sgn in (("stb",-1),("port",1)):
    pts=[]
    for xmm in np.arange(3000,5451,10):
        px=int(round(XB-xmm/S))
        y0=np.interp(xmm,seed_x,seed_y)
        pc=YC-sgn*y0/S
        lo,hi=int(pc-9),int(pc+9)     # +-38 mm window
        col=im[lo:hi+1,px-1:px+2].astype(float).mean(axis=1)
        j=int(np.argmin(col))
        if col[j]<150 and (np.median(col)-col[j])>45:
            py=lo+j
            # sub-pixel centroid
            w=np.clip(np.median(col)-col[max(j-2,0):j+3],0,None)
            if w.sum()>0: py=lo+max(j-2,0)+float((w*np.arange(len(w))).sum()/w.sum())
            pts.append((float(xmm),float(sgn*(YC-py)*S)))
    out[side]=pts
    a=np.array(pts)
    print(side,len(pts))
    for xb in range(3000,5451,250):
        m=(a[:,0]>=xb-60)&(a[:,0]<=xb+60)
        if m.any(): print("  x %d: |y| median %.0f (n %d, spread %.0f)"%(xb,np.median(np.abs(a[m,1])),m.sum(),np.ptp(np.abs(a[m,1]))))
json.dump(out,open(sys.argv[1],"w"))
