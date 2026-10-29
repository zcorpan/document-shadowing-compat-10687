"""Load each URL in Firefox Nightly with the detection preload and record which shadowing names the
top-level document reads or writes while a matching named element exists.

Usage: detect.py URLS.txt OUT.jsonl [workers]
Resumable: skips URLs already in OUT.jsonl.
"""
import json, os, sys, threading, queue, concurrent.futures as cf
from ff import Browser, scrub

PAGE_TIMEOUT = 75


def worker(q, out, lock):
    b = None
    while True:
        try:
            url = q.get_nowait()
        except queue.Empty:
            break
        rec = {"url": url}
        try:
            if b is None:
                b = Browser(block=False, preload=True)
            with cf.ThreadPoolExecutor(1) as ex:
                r = ex.submit(b.visit, url, 6).result(timeout=PAGE_TIMEOUT)
            rec["load_error"] = r["load_error"]
            rec["shadow"] = [dict(e, stack=scrub(e["stack"])) for k, e in r["events"] if k == "shadow"]
        except Exception as ex:
            rec["load_error"] = type(ex).__name__
            rec["shadow"] = []
            if b:
                threading.Thread(target=b.quit, daemon=True).start()
            b = None
        with lock:
            out.write(json.dumps(rec) + "\n")
            out.flush()
        print(len(rec["shadow"]), rec.get("load_error"), url, flush=True)
    if b:
        b.quit()


def main():
    urls_file, out_file = sys.argv[1], sys.argv[2]
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    done = set()
    if os.path.exists(out_file):
        done = {json.loads(l)["url"] for l in open(out_file)}
    q = queue.Queue()
    for u in dict.fromkeys(l.strip() for l in open(urls_file)):
        if u and u not in done:
            q.put(u)
    lock = threading.Lock()
    with open(out_file, "a") as out:
        ts = [threading.Thread(target=worker, args=(q, out, lock)) for _ in range(n)]
        for t in ts:
            t.start()
        for t in ts:
            t.join()


if __name__ == "__main__":
    main()
