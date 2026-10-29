"""Run test/preload-test.html in Firefox Nightly: today's behavior without and with the preload
(results must match, and the preload must log the shadowed accesses), and the blocking pref."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ff import Browser

URL = "file://" + os.path.join(os.path.dirname(os.path.abspath(__file__)), "preload-test.html")
out = {}
for label, block, preload in [("off", False, False), ("on", True, False), ("off+preload", False, True)]:
    b = Browser(block, preload)
    out[label] = b.visit(URL, settle=2)
    b.quit()
for label, r in out.items():
    print("==", label, r["load_error"])
    for kind, e in r["events"]:
        print(" ", kind, json.dumps(e) if kind != "shadow" else (e["op"], e["name"], e["tags"], e["count"], e["readyState"]))
res = {k: [{p: x for p, x in e.items() if p != "ownKeys"} for kind, e in v["events"] if kind == "result"]
       for k, v in out.items()}
# The preload returns prototype values, so it should match the blocking pref (Object.keys differs:
# the preload's accessors are non-enumerable).
print("on == off+preload (except ownKeys):", res["on"] == res["off+preload"])
names = sorted({(e["op"], e["name"]) for kind, e in out["off+preload"]["events"] if kind == "shadow"})
print("logged:", names)
