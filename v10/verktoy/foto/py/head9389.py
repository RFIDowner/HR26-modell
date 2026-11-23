"""Fryst modell for kameraet i IMG_9389.

Hovedoekta endrer hr26/params.py mens trinn 5 tilpasses (kjolens hulkil,
spantene forut, senterlinjen). Kameraet skal ikke flytte seg med det, saa
cam9389.py bygger trekkene (liste, kjol, ror, venstre omriss, vindu, stripe
akter) fra en fast commit: hr26/ og data/ hentes med `git show` til
%TEMP%/hr26_<ref>/ og importeres som pakken hr26 FOER common.py.

  import head9389          # foer common / uwlib / geo9389
  head9389.REF             # commit (miljoevariabel HR26_REF, standard 0976477;
                           # HR26_REF=work bruker arbeidskopien)
"""
import os
import subprocess
import sys
import tempfile

REF = os.environ.get("HR26_REF", "0976477")
_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))


def _extract(ref):
    root = os.path.join(tempfile.gettempdir(), "hr26_" + ref)
    done = os.path.join(root, ".ok")
    if os.path.exists(done):
        return root
    names = subprocess.run(["git", "-C", _REPO, "ls-tree", "-r", "--name-only", ref, "hr26", "data"],
                           check=True, capture_output=True, text=True).stdout.split()
    for n in names:
        dst = os.path.join(root, *n.split("/"))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        blob = subprocess.run(["git", "-C", _REPO, "show", ref + ":" + n], check=True, capture_output=True).stdout
        with open(dst, "wb") as fh:
            fh.write(blob)
    open(done, "w").close()
    return root


if REF != "work" and "hr26" not in sys.modules:
    _root = _extract(REF)
    sys.path.insert(0, _root)
    import hr26  # noqa: F401,E402  (pakken fra commit REF)
    assert os.path.dirname(hr26.__file__).startswith(_root), hr26.__file__
    sys.path.remove(_root)
    sys.path.append(_root)      # undermoduler finnes via hr26.__path__
