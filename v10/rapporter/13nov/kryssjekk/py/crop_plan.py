import sys
from PIL import Image, ImageDraw
S=4.2591; XB=2240.1; YC=1333.2
im=Image.open(r"C:/Users/stig/Documents/Seilbåt/Hallberg-Rassy-kilder/HR26interior448-5.jpeg").convert("L")
x0,x1=1040,1500; y0,y1=1080,1590
c=im.crop((x0,y0,x1,y1)).resize(((x1-x0)*2,(y1-y0)*2),Image.LANCZOS).convert("RGB")
d=ImageDraw.Draw(c)
for ymm,col in ((418,(255,0,0)),(-418,(255,0,0)),(250,(0,160,0)),(-250,(0,160,0)),(0,(0,0,255))):
    py=(YC-ymm/S-y0)*2
    d.line([(0,py),(c.width,py)],fill=col,width=1)
for xmm in (3450,3600,4000,4500,4900,5446):
    px=(XB-xmm/S-x0)*2
    d.line([(px,0),(px,c.height)],fill=(255,128,0),width=1); d.text((px+3,5),str(xmm),fill=(255,128,0))
c.save(sys.argv[1])
print(c.size)
