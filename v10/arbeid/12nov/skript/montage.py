import sys
from PIL import Image
out, cols, w = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
ims = [Image.open(p).convert('RGB') for p in sys.argv[4:]]
ims = [im.resize((w, int(im.height * w / im.width))) for im in ims]
rows = (len(ims) + cols - 1) // cols
h = max(im.height for im in ims)
sheet = Image.new('RGB', (cols * w, rows * h), 'white')
for i, im in enumerate(ims):
    sheet.paste(im, ((i % cols) * w, (i // cols) * h))
sheet.save(out)
print(sheet.size)
