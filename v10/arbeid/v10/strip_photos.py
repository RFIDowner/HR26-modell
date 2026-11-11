"""Kopierer bildene uten metadata (EXIF/GPS), rettet etter orientering, maks 2400 px."""
import glob, os, sys
from PIL import Image, ImageOps
src, dst = sys.argv[1], sys.argv[2]
for p in sorted(glob.glob(os.path.join(src, "IMG_*.jpeg"))):
    im = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
    im.thumbnail((2400, 2400), Image.LANCZOS)
    out = os.path.join(dst, os.path.basename(p).replace(".jpeg", ".jpg"))
    clean = Image.new("RGB", im.size); clean.paste(im)
    clean.save(out, "JPEG", quality=88, optimize=True)
    chk = Image.open(out)
    print(os.path.basename(out), clean.size, f"{os.path.getsize(out)/1e3:.0f} kB", "exif:", len(chk.getexif()), "info:", sorted(chk.info.keys()))
