"""Find pages where a named element's name matches a property that the page's scripts added to
`document`'s prototype chain (`Object.getPrototypeOf(document)` up to `Object.prototype`).

Loads each URL in Firefox Nightly (pref off), then compares each prototype's own property names
against the same prototypes on a baseline page.

Usage: detect_expando.py URLS.txt OUT.jsonl [workers]
Resumable: skips URLs already in OUT.jsonl.
"""
import json, os, sys, threading, queue, concurrent.futures as cf
from ff import Browser

PAGE_TIMEOUT = 75
BASELINE_URL = "https://example.com/"

PROBE = """
const out = [];
for (let p = Object.getPrototypeOf(document); p; p = Object.getPrototypeOf(p)) {
  const ctor = Object.getOwnPropertyDescriptor(p, "constructor");
  out.push({proto: ctor && typeof ctor.value === "function" ? ctor.value.name : "?",
            names: Object.getOwnPropertyNames(p)});
}
const named = new Set();
for (const el of document.querySelectorAll("embed[name], form[name], iframe[name], img[name], object[name]"))
  if (el.namespaceURI === "http://www.w3.org/1999/xhtml" && el.name !== "") named.add(el.getAttribute("name"));
for (const el of document.querySelectorAll("object[id], img[id][name]:not([name=''])"))
  if (el.namespaceURI === "http://www.w3.org/1999/xhtml" && el.id !== "") named.add(el.id);
return {protos: out, named: [...named]};
"""


def probe(b):
    return b.d.execute_script(PROBE)


def worker(q, out, lock, baseline):
    b = None
    while True:
        try:
            url = q.get_nowait()
        except queue.Empty:
            break
        rec = {"url": url}
        try:
            if b is None:
                b = Browser(block=False)
            with cf.ThreadPoolExecutor(1) as ex:
                r = ex.submit(b.visit, url, 6).result(timeout=PAGE_TIMEOUT)
                p = ex.submit(probe, b).result(timeout=20)
            rec["load_error"] = r["load_error"]
            added = {}
            for entry in p["protos"]:
                base = baseline.get(entry["proto"], set())
                new = sorted(set(entry["names"]) - base)
                if new:
                    added[entry["proto"]] = new
            rec["added"] = added
            all_added = {n for names in added.values() for n in names}
            rec["named"] = sorted(p["named"])
            rec["hits"] = sorted(all_added & set(p["named"]))
        except Exception as ex:
            rec["load_error"] = type(ex).__name__
            if b:
                threading.Thread(target=b.quit, daemon=True).start()
            b = None
        with lock:
            out.write(json.dumps(rec) + "\n")
            out.flush()
        print(rec.get("hits"), rec.get("load_error"), url, flush=True)
    if b:
        b.quit()


def main():
    urls_file, out_file = sys.argv[1], sys.argv[2]
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    b = Browser(block=False)
    b.visit(BASELINE_URL, 1)
    baseline = {e["proto"]: set(e["names"]) for e in probe(b)["protos"]}
    b.quit()
    done = set()
    if os.path.exists(out_file):
        done = {json.loads(l)["url"] for l in open(out_file)}
    q = queue.Queue()
    for u in dict.fromkeys(l.strip() for l in open(urls_file)):
        if u and u not in done:
            q.put(u)
    lock = threading.Lock()
    with open(out_file, "a") as out:
        ts = [threading.Thread(target=worker, args=(q, out, lock, baseline)) for _ in range(n)]
        for t in ts:
            t.start()
        for t in ts:
            t.join()


if __name__ == "__main__":
    main()
