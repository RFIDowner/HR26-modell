import sys, os, pymupdf
src, out = sys.argv[1], sys.argv[2]
for name in sorted(os.listdir(src)):
    p = os.path.join(src, name)
    if not name.lower().endswith('.pdf'):
        continue
    doc = pymupdf.open(p)
    print(f'== {name}: {doc.page_count} sider')
    for i, page in enumerate(doc):
        imgs = page.get_images(full=True)
        txt = page.get_text().strip().replace('\n', ' ')[:110]
        dims = [(x[2], x[3]) for x in imgs]
        print(f'  s{i+1}: {page.rect.width:.0f}x{page.rect.height:.0f}pt, bilder {dims[:6]}, tekst: {txt}')
        pix = page.get_pixmap(dpi=60)
        pix.save(os.path.join(out, f'{os.path.splitext(name)[0]}_s{i+1}.png'))
