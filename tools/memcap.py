"""memcap.py - kjoer et program med et hardt minnetak (Windows Job Object).

Bruk:  python memcap.py [--gb 5] [--lock] -- python skript.py arg ...

* --gb N   prosessen (og barna) faar hoeyst N GB commit; over det feiler
           allokeringen (MemoryError i Python) i stedet for at PC-en krasjer.
* --lock   bare EN slik jobb om gangen paa maskinen (fil-laas); andre venter.
Avslutter med barnets returkode. Skriver toppbruken (peak) til stderr.
"""
import ctypes, ctypes.wintypes as wt, os, subprocess, sys, time, msvcrt

k32 = ctypes.WinDLL("kernel32", use_last_error=True)

class IO_COUNTERS(ctypes.Structure):
    _fields_ = [(n, ctypes.c_ulonglong) for n in (
        "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
        "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

class BASIC(ctypes.Structure):
    _fields_ = [("PerProcessUserTimeLimit", ctypes.c_longlong),
                ("PerJobUserTimeLimit", ctypes.c_longlong),
                ("LimitFlags", wt.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wt.DWORD),
                ("Affinity", ctypes.c_size_t), ("PriorityClass", wt.DWORD),
                ("SchedulingClass", wt.DWORD)]

class EXT(ctypes.Structure):
    _fields_ = [("BasicLimitInformation", BASIC), ("IoInfo", IO_COUNTERS),
                ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]

JOB_OBJECT_LIMIT_JOB_MEMORY = 0x200
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
JobObjectExtendedLimitInformation = 9
PROCESS_ALL = 0x1F0FFF

def main():
    a = sys.argv[1:]
    gb, lock = 5.0, False
    while a and a[0] != "--":
        if a[0] == "--gb": gb = float(a[1]); a = a[2:]
        elif a[0] == "--lock": lock = True; a = a[1:]
        else: break
    if a and a[0] == "--": a = a[1:]
    if not a: print(__doc__); return 2
    lf = None
    if lock:
        lp = os.path.join(os.environ.get("TEMP", "."), "hr26_cad.lock")
        lf = open(lp, "a+")
        t0 = time.time()
        while True:
            try:
                lf.seek(0); msvcrt.locking(lf.fileno(), msvcrt.LK_NBLCK, 1); break
            except OSError:
                if time.time() - t0 > 7200: print("memcap: ga opp aa vente paa laasen", file=sys.stderr); return 3
                time.sleep(5)
    job = k32.CreateJobObjectW(None, None)
    info = EXT()
    info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_JOB_MEMORY | JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    info.JobMemoryLimit = int(gb * 1024**3)
    if not k32.SetInformationJobObject(job, JobObjectExtendedLimitInformation, ctypes.byref(info), ctypes.sizeof(info)):
        raise ctypes.WinError(ctypes.get_last_error())
    env = dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")
    p = subprocess.Popen(a, env=env, creationflags=0x4)   # CREATE_SUSPENDED
    h = k32.OpenProcess(PROCESS_ALL, False, p.pid)
    if not k32.AssignProcessToJobObject(job, h):
        p.kill(); raise ctypes.WinError(ctypes.get_last_error())
    # gjenoppta hovedtraaden (NtResumeProcess)
    ctypes.WinDLL("ntdll").NtResumeProcess(h)
    rc = p.wait()
    q = EXT(); k32.QueryInformationJobObject(job, JobObjectExtendedLimitInformation, ctypes.byref(q), ctypes.sizeof(q), None)
    print(f"memcap: topp {q.PeakJobMemoryUsed/1024**3:.2f} GB av {gb:.1f} GB, rc={rc}", file=sys.stderr)
    return rc

if __name__ == "__main__":
    sys.exit(main())
