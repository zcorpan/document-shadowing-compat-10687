"""Flag pages whose blocking run (B) differs from today's behavior (A) beyond the noise between the
two runs of today's behavior (A, A2): new JS errors, body text length, scroll size, screenshot.

Usage: ffanalyze.py OUTDIR > flags.json
"""
import json, os, re, sys
from PIL import Image, ImageChops

outdir = sys.argv[1]


def norm(e):
    return re.sub(r"\d+", "N", e)


def diff_ratio(a, b):
    try:
        ia, ib = Image.open(a).convert("L"), Image.open(b).convert("L")
    except Exception:
        return None
    if ia.size != ib.size:
        return 1.0
    ia, ib = ia.resize((ia.width // 4, ia.height // 4)), ib.resize((ib.width // 4, ib.height // 4))
    d = ImageChops.difference(ia, ib).point(lambda v: 255 if v > 24 else 0)
    return sum(1 for v in d.getdata() if v) / (d.width * d.height)


rows = []
for l in open(os.path.join(outdir, "results.jsonl")):
    r = json.loads(l)
    A, A2, B = r["A"], r["A2"], r["B"]
    shots = {k: os.path.join(outdir, "shots", f"{r['id']}-{k}.png") for k in ("A", "A2", "B")}
    row = {"url": r["url"], "id": r["id"], "load_error": [A.get("load_error"), A2.get("load_error"), B.get("load_error")]}
    if all("text" in x for x in (A, A2, B)):
        ea = {norm(e) for e in A["errors"]} | {norm(e) for e in A2["errors"]}
        row["new_errors"] = sorted({norm(e) for e in B["errors"]} - ea)
        row["gone_errors"] = sorted(({norm(e) for e in A["errors"]} & {norm(e) for e in A2["errors"]})
                                    - {norm(e) for e in B["errors"]})
        noise_t = abs(A["text"] - A2["text"])
        row["text_change"] = abs(B["text"] - A["text"]) > max(noise_t * 2, 0.05 * max(A["text"], 1))
        noise_h = abs(A["h"] - A2["h"])
        row["height_change"] = abs(B["h"] - A["h"]) > max(noise_h * 2, 50)
        row["form_img_change"] = (A["forms"], A["imgs"]) != (B["forms"], B["imgs"])
        n = diff_ratio(shots["A"], shots["A2"])
        d = diff_ratio(shots["A"], shots["B"])
        row["pixels"] = [n, d]
        row["pixel_change"] = n is not None and d is not None and d > max(2 * n, 0.01)
        row["flag"] = bool(row["new_errors"] or row["gone_errors"] or row["text_change"]
                           or row["height_change"] or row["pixel_change"])
    else:
        row["flag"] = None
    rows.append(row)
json.dump(rows, sys.stdout, indent=1)
print(f"\n{len(rows)} pages, {sum(r['flag'] is True for r in rows)} flagged, "
      f"{sum(r['flag'] is None for r in rows)} not measurable", file=sys.stderr)
