"""Felles stier og import av modellen. Kopiert inn i repoet 13.11.2026 fra
kontroll-oekta (undervann), med stier relativt til repoet."""
import importlib, json, os, sys
import numpy as np
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
OLD = REPO + "/v10/arbeid"          # t9388_auto: OLD + "/undervann/traces/..." -> se T9388_AUTO
W = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))   # out/ ligger her
SRC = r"C:/Users/stig/Documents/Seilbåt/Hallberg-Rassy-kilder"
FOTO = REPO + "/docs/foto"
if REPO not in sys.path:
    sys.path.insert(0, REPO)
from hr26 import params as P          # noqa
from hr26 import curves as C          # noqa

ELINES = json.load(open(REPO + "/v10/rapporter/12nov/enderlein_lines.json"))
T9388_AUTO = REPO + "/v10/arbeid/12nov/undervann/t9388_auto.json"


def reload_model(**over):
    """Set params (P.X = v) and rebuild curves' module-level splines."""
    for k, v in over.items():
        setattr(P, k, v)
    global C
    C = importlib.reload(sys.modules["hr26.curves"])
    return C


def eline(name):
    return np.asarray(ELINES["profile"][name]["xz"], float)


def save_json(obj, path):
    def conv(o):
        if isinstance(o, np.ndarray):
            return o.tolist()
        if isinstance(o, np.floating):
            return float(o)
        if isinstance(o, np.integer):
            return int(o)
        raise TypeError(type(o))
    with open(path, "w") as fh:
        json.dump(obj, fh, default=conv, indent=1)
