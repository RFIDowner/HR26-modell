import sys
from PIL import Image, ImageDraw, ImageOps
S=4.2591; XB=2240.1; YD=541.8
im=Image.open(r"C:/Users/stig/Documents/Seilbåt/Hallberg-Rassy-kilder/HR26interior448-5.jpeg").convert("L")
x0,x1,y0,y1=[int(v) for v in sys.argv[2:6]]; sc=float(sys.argv[6])
c=im.crop((x0,y0,x1,y1)); c=ImageOps.autocontrast(c,cutoff=1)
c=c.resize((int((x1-x0)*sc),int((y1-y0)*sc)),Image.LANCZOS).convert("RGB")
d=ImageDraw.Draw(c)
for xmm in range(0,8001,250):
    px=(XB-xmm/S-x0)*sc
    if 0<=px<c.width:
        d.line([(px,0),(px,c.height)],fill=(255,170,170) if xmm%500 else (255,60,60),width=1); d.text((px+2,2),str(xmm),fill=(220,0,0))
for zmm in range(-1500,1501,50):
    py=(YD-zmm/S-y0)*sc
    if 0<=py<c.height:
        d.line([(0,py),(c.width,py)],fill=(190,190,255) if zmm%100 else (80,80,255),width=1)
        if zmm%100==0: d.text((2,py+1),str(zmm),fill=(0,0,220))
c.save(sys.argv[1]); print(c.size)
