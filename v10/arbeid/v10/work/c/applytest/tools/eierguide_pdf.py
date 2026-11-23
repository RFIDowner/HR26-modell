"""Lager EIERGUIDE.pdf (A4) av EIERGUIDE.md, med bilder fra docs/images.

  pip install markdown
  python tools/eierguide_pdf.py

Trenger Chromium (headless). Sti kan settes med miljovariabelen CHROME.
"""
import os
import re
import subprocess
import sys
import tempfile

import markdown

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
CHROME = os.environ.get("CHROME", "/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
WIDTH = {"overlegg-profil.jpg": 100, "eier-baug.jpg": 68, "skilt.jpg": 52}

CSS = """
@page { size: A4; margin: 17mm 18mm 18mm 18mm; }
body { font-family: "Liberation Sans", Arial, sans-serif; font-size: 10pt; line-height: 1.36; color: #111; }
h1 { font-size: 21pt; margin: 0 0 4mm 0; border-bottom: 2px solid #111; padding-bottom: 3mm; }
h1.ny-side { break-before: page; }
h2 { font-size: 13.5pt; margin: 5mm 0 2mm 0; break-after: avoid; }
section { margin: 0 0 5mm 0; break-inside: avoid; }
section h2 { margin-top: 0; }
p { margin: 0 0 2.4mm 0; }
ul, ol { margin: 0 0 2.5mm 0; padding-left: 6mm; }
li { margin-bottom: 1mm; }
p, li, figure, table { break-inside: avoid; }
table { border-collapse: collapse; margin: 0 0 3mm 0; font-size: 10pt; }
th, td { border: 0.5pt solid #777; padding: 1.2mm 2.5mm; text-align: left; vertical-align: top; }
th { background: #eee; }
figure { margin: 2mm 0 4mm 0; }
figure img { width: 100%; border: 0.4pt solid #999; display: block; }
figcaption { font-size: 8.5pt; color: #333; margin-top: 1mm; }
.rad { display: flex; gap: 4mm; align-items: flex-start; margin: 2mm 0 4mm 0; }
.rad figure { flex: 1; margin: 0; }
"""


def fig(alt, src):
    name = os.path.basename(src)
    w = WIDTH.get(name)
    style = f' style="width:{w}%"' if w else ""
    path = os.path.join(ROOT, src)
    return f'<figure{style}><img src="file://{path}"><figcaption>{alt}</figcaption></figure>'


def main():
    md = open(os.path.join(ROOT, "EIERGUIDE.md"), encoding="utf-8").read()
    html = markdown.markdown(md, extensions=["extra"])
    img = r'<img alt="([^"]*)" src="([^"]*)" ?/?>'

    def para(m):
        items = re.findall(img, m.group(1))
        if len(items) == 1:
            return fig(*items[0])
        return '<div class="rad">' + "".join(fig(*i) for i in items) + "</div>"

    html = re.sub(r"<p>((?:\s*" + img + r"\s*)+)</p>", para, html)
    # andre hovedoverskrift starter paa ny side
    first = html.find("<h1>")
    second = html.find("<h1>", first + 1)
    if second > 0:
        html = html[:second] + '<h1 class="ny-side">' + html[second + 4:]
        head, tail = html[:second], html[second:]
        parts = re.split(r"(?=<h2>)", head)
        head = parts[0] + "".join(f"<section>{p}</section>" for p in parts[1:])
        # i innsiktskapitlet holdes alle deler samlet unntatt den lange "Valgene"
        tparts = re.split(r"(?=<h2>)", tail)
        tail = tparts[0] + "".join(
            p if p.startswith("<h2>Valgene") else f"<section>{p}</section>" for p in tparts[1:]
        )
        html = head + tail
    doc = f'<!doctype html><html lang="no"><head><meta charset="utf-8"><title>Eierguide</title><style>{CSS}</style></head><body>{html}</body></html>'
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as fh:
        fh.write(doc)
        tmp = fh.name
    out = os.path.join(ROOT, "EIERGUIDE.pdf")
    subprocess.run([CHROME, "--headless=new", "--no-sandbox", "--disable-gpu", "--allow-file-access-from-files",
                    "--no-pdf-header-footer", f"--print-to-pdf={out}", f"file://{tmp}"],
                   check=True, capture_output=True)
    os.unlink(tmp)
    print("skrev", out)


if __name__ == "__main__":
    sys.exit(main())
