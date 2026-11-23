"""Dump sections/profile/hydro for the model imported from argv[1] (repo path) to argv[2] json."""
import sys
sys.path.insert(0, sys.argv[1])
from hr26 import params as P, curves as C
sys.path.insert(1, '.')
import numpy as np
import common as c, uwlib as U
import os
assert os.path.normcase(os.path.abspath(C.__file__)).startswith(os.path.normcase(os.path.abspath(sys.argv[1]))), C.__file__
xs_body = [500.0, 1000.0, 1500.0, 2000.0, 2900.0, 3500.0, 4300.0, 5000.0, 5600.0, 6100.0, 6600.0, 7100.0, 7500.0, 7750.0]
out = dict(sections={str(x): np.array(C.section(x, 300)).tolist() for x in xs_body},
           profile=[[float(x), float(C.bottom_z(x))] for x in np.arange(0, 7951, 10.0)],
           hydro=U.hydro(), wl=[[float(x), float(C.wl_half_breadth(x))] for x in np.arange(1000, 7850, 50.0)])
# topsides above the strake for change check
out["top"] = {str(x): np.array(C.section(float(x), 400)).tolist() for x in np.arange(300, 7801, 250.0)}
out["strake"] = {str(x): float(C.strake_z(float(x))) for x in np.arange(300, 7801, 250.0)}
c.save_json(out, sys.argv[2])
print(sys.argv[2], out["hydro"])
