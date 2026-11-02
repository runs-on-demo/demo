"""Prints where the time goes from a job's queueing to its first step, per
kind of runner, from the timing marks each job saved (see v4-startup.yml)."""
import json, pathlib, re, statistics, sys
from datetime import datetime, timedelta

ORDER = ["job-queued", "sandbox-created", "instance-created", "assigned", "instance-booted",
         "sandboxd-started", "host-ready", "assignment-received", "host-setup-done",
         "runner-started", "runner-connected", "runner-listening", "job-received",
         "worker-started", "step-started"]

def ts(s):
    s = s.replace("Z", "").replace("T", " ")
    return datetime.strptime(s[:23], "%Y-%m-%d %H:%M:%S.%f" if "." in s else "%Y-%m-%d %H:%M:%S")

def marks(rec):
    out = {}
    for detail in rec["groups"]:
        base = None
        for line in detail.splitlines():
            if line.startswith("From "):
                base = ts(line[5:].strip())
                continue
            m = re.match(r"\s*([\d.]+)s\s+(?:\+[\d.]+s\s+)?(\S+)$", line)
            if m and base:
                out[m.group(2)] = base + timedelta(seconds=float(m.group(1)))
    out["step-started"] = ts(rec["step_started"])
    return out

def pct(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(p * (len(xs) - 1))))]

jobs = {j["name"]: j for j in json.load(open(sys.argv[2]))["jobs"]}
kinds = {}
for f in sorted(pathlib.Path(sys.argv[1]).glob("*.json")):
    rec = json.load(open(f))
    m = marks(rec)
    kinds.setdefault(rec["kind"], []).append(m)

for kind, runs in kinds.items():
    print(f"\n== {kind} (n={len(runs)})")
    seg = {}
    totals = []
    for m in runs:
        q = m.get("job-queued")
        if not q:
            continue
        seq = [n for n in ORDER if n in m and m[n] >= q]
        for a, b in zip(seq, seq[1:]):
            seg.setdefault(f"{a} -> {b}", []).append((m[b] - m[a]).total_seconds())
        totals.append((m["step-started"] - q).total_seconds())
    width = max(len(k) for k in seg) if seg else 10
    print(f"{'segment':<{width}}  {'n':>3} {'p50':>6} {'p90':>6} {'max':>6}")
    for k in sorted(seg, key=lambda k: ORDER.index(k.split(' -> ')[0]) if k.split(' -> ')[0] in ORDER else 99):
        v = seg[k]
        print(f"{k:<{width}}  {len(v):>3} {pct(v, .5):>6.2f} {pct(v, .9):>6.2f} {max(v):>6.2f}")
    if totals:
        print(f"{'queued -> first step':<{width}}  {len(totals):>3} {pct(totals, .5):>6.2f} {pct(totals, .9):>6.2f} {max(totals):>6.2f}")
