"""Recompute the README's numbers from the committed data. Writes data/summary.json."""
import csv, collections, json
from props import CATEGORY, kind

s = {}
rows = list(csv.DictReader(open("queries/4872-pages.csv")))
s["httparchive_totals"] = {r["client"]: int(r["rank"]) for r in rows if r["page"] == "(total)"}
hits = [r for r in rows if r["page"] != "(total)"]
s["httparchive_4872_rows"] = dict(collections.Counter(r["client"] for r in hits))
s["httparchive_4872_distinct_pages"] = len({r["page"] for r in hits})

cc = json.load(open("data/cc-hits.jsonl.totals.json"))
cch = [json.loads(l) for l in open("data/cc-hits.jsonl")]
s["cc_pages"] = cc["pages"]
s["cc_pages_with_shadowing_named_element"] = len(cch)
s["cc_by_category_kind"] = dict(collections.Counter(
    f"{c}/{k}" for h in cch for c, k in {(e["category"], e["kind"]) for e in h["elements"]}))
s["cc_names"] = dict(collections.Counter(n for h in cch for n in {e["name"] for e in h["elements"]}))
s["cc_pages_with_inline_ref"] = sum(bool(h["inline_refs"]) for h in cch)

for label, f in [("detect_httparchive", "data/detect-httparchive.jsonl"), ("detect_cc", "data/detect-cc.jsonl")]:
    recs = [json.loads(l) for l in open(f)]
    d = {"pages": len(recs), "load_errors": sum(bool(r["load_error"]) for r in recs),
         "pages_with_access": sum(bool(r["shadow"]) for r in recs)}
    d["names"] = dict(collections.Counter(n for r in recs for n in {e["name"] for e in r["shadow"]}).most_common())
    d["by_category_kind"] = dict(collections.Counter(
        f"{CATEGORY[n]}/{kind(n)}" for r in recs for n in {e["name"] for e in r["shadow"]}))
    s[label] = d

recs = [json.loads(l) for l in open("data/detect-expando-httparchive.jsonl")]
s["detect_expando_httparchive"] = {
    "pages": len(recs), "load_errors": sum(bool(r["load_error"]) for r in recs),
    "pages_adding_to_prototypes": sum(bool(r["added"]) for r in recs),
    "pages_with_named_elements": sum(bool(r["named"]) for r in recs),
    "pages_with_hits": sum(bool(r["hits"]) for r in recs)}

res = [json.loads(l) for l in open("out/results.jsonl")]
s["compare_pages"] = len(res)
s["compare_flagged"] = sum(r["flag"] is True for r in json.load(open("out/flags.json")))
s["ratings"] = dict(collections.Counter(r["rating"] for r in csv.DictReader(open("review/ratings.csv"))))
json.dump(s, open("data/summary.json", "w"), indent=1)
print(json.dumps(s, indent=1))
