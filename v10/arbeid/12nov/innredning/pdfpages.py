"""Henter sider fra en PDF som PNG og skriver ut teksten.
Bruk: python -I pdfpages.py <pdf> <utmappe> <fra> <til> [zoom]"""
import sys
import fitz

pdf, out, a, b = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
zoom = float(sys.argv[5]) if len(sys.argv) > 5 else 1.5
doc = fitz.open(pdf)
print("sider:", doc.page_count)
for i in range(a - 1, min(b, doc.page_count)):
    p = doc[i]
    pix = p.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    fn = f"{out}/side{i + 1}.png"
    pix.save(fn)
    print(fn, pix.width, pix.height)
    print("--- tekst side", i + 1)
    print(p.get_text()[:3000])
