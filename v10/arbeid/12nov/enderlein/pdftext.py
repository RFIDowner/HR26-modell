"""Print the text of the HR 26 PDFs (specs: LOA, LWL, beam, draft ...)."""
import os
import sys

import fitz

SRC = os.path.join(os.path.expanduser("~"), "Documents", "Seilbåt", "Hallberg-Rassy-kilder")

for fn in sys.argv[1:]:
    d = fitz.open(os.path.join(SRC, fn))
    print("=====", fn, d.page_count)
    for i, p in enumerate(d):
        t = p.get_text()
        if t.strip():
            print("--- page", i + 1)
            print(t[:4000])
