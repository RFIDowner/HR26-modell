import sys, importlib
REP = sys.argv[1]
sys.path.insert(0, REP)
from hr26 import params as P, curves as C
sys.path.insert(1, '.')
import numpy as np
import common as c, uwlib as U, photos as PH
def run(tag, **over):
    for k, v in over.items():
        setattr(P, k, v)
    importlib.reload(sys.modules["hr26.curves"]); c.C = sys.modules["hr26.curves"]
    PH.summary(tag)
base = dict(SECTION_DEADRISE=list(P.SECTION_DEADRISE), SECTION_N=list(P.SECTION_N))
run("patch")
DRb = [(0.00, 45.0), (0.127, 15.0), (0.20, 4.0), (0.30, 4.0), (0.45, 6.0), (0.60, 16.0), (0.75, 26.0), (0.90, 15.0), (1.00, 3.0)]
run("dr45=6 dr60=16", SECTION_DEADRISE=DRb)
DRc = [(0.00, 45.0), (0.127, 15.0), (0.20, 4.0), (0.30, 4.0), (0.45, 8.0), (0.60, 18.0), (0.75, 27.0), (0.90, 15.0), (1.00, 3.0)]
run("dr45=8 dr60=18", SECTION_DEADRISE=DRc)
run("dr45=8 dr60=18 N3.7", SECTION_DEADRISE=DRc, SECTION_N=[(0.00, 2.4), (0.15, 3.1), (0.30, 3.4), (0.45, 3.7), (0.80, 3.8), (1.00, 3.6)])
