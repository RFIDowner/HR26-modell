import sys
from PIL import Image, ImageDraw, ImageOps
S=4.2591; XB=2240.1; YC=1333.2
im=Image.open(r"C:/Users/stig/Documents/Seilbåt/Hallberg-Rassy-kilder/HR26interior448-5.jpeg").convert("L")
x0,x1,y0,y1=[int(v) for v in sys.argv[2:6]]; sc=float(sys.argv[6])
c=im.crop((x0,y0,x1,y1))
c=ImageOps.autocontrast(c,cutoff=1)
c=c.resize((int((x1-x0)*sc),int((y1-y0)*sc)),Image.LANCZOS).convert("RGB")
d=ImageDraw.Draw(c)
for xmm in range(0,8001,500):
    px=(XB-xmm/S-x0)*sc
    if 0<=px<c.width:
        d.line([(px,0),(px,12)],fill=(255,0,0),width=2); d.text((px+2,14),str(xmm),fill=(255,0,0))
for ymm in range(-1400,1401,200):
    py=(YC-ymm/S-y0)*sc
    if 0<=py<c.height:
        d.line([(0,py),(10,py)],fill=(0,0,255),width=2); d.text((12,py-5),str(ymm),fill=(0,0,255))
c.save(sys.argv[1]); print(c.size)
