import sys, json; sys.path.insert(0, '.')
import numpy as np
import common as c, opt2
q0 = [2.0, 6.0, 12.0, 22.0, 26.0, 16.0, 4.0, 3.8, 3.8, -340.0, -220.0, 220.0]
lb = [0, 0, 0, 0, 0, 0, 0, 2.8, 2.8, -460, -330, 120]
ub = [30, 30, 30, 30, 30, 30, 30, 4.2, 4.2, -300, -150, 420]
q, info = opt2.run("C smooth3 w88=0.2", q0, lb, ub, 3.0, 0.2)
c.save_json(dict(q=q, vol=info["vol"], top=info["top"]), c.W + "/out/opt3.json")
