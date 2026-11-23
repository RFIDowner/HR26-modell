import sys; sys.path.insert(0, '.')
import numpy as np
from scipy.optimize import least_squares
import cam9391 as K, uwlib as U
p = np.array([9423.16, 4.58, -323.89, 175.8, -0.49, 1.78, 1271.95, 127.54, 53.0])
g = K.residuals(p, True)
print("strake resid by u:", [(int(u), round(r, 1)) for u, r in zip(K.st_c[::4, 0], g["strake"][::4])])
cam = U.Cam(p[:7], 1500, 2000)
u, v, z = cam.project(K.STRAKE3); print("model strake u range", u.min(), u.max())
# variant: strake height free, f fixed at 1495
def res2(q, parts=False):
    zs = q[9]
    K.STRAKE3 = K.tline(zs, dx=13.0)
    pp = np.r_[q[:9]]
    r = K.residuals(pp, parts)
    return r
for fprior in (True,):
    best = None
    for s in ([9700, 0, -120, 176, 5, 1, 1495, 140, 0, 805], [9423, 4, -324, 175.8, -0.5, 1.8, 1495, 127, 0, 805], [10000, 0, -300, 176, 3, 1.5, 1495, 140, 0, 700]):
        r = least_squares(res2, s, bounds=([8300, -1500, -1300, 160, -20, -15, 1100, 0, -100, 500], [14000, 1500, 1500, 190, 30, 15, 2200, 400, 100, 1000]),
                          x_scale=[200, 50, 100, 1, 1, 1, 50, 20, 10, 20], loss="soft_l1", f_scale=4.0, max_nfev=400)
        gg = res2(r.x, True)
        print(np.round(r.x, 1).tolist(), round(r.cost, 1), {k: round(K.rms(v), 1) for k, v in gg.items()})
