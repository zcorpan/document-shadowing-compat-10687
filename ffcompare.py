"""Before/after comparison in Firefox Nightly: today's behavior twice (A, A2), then the blocking pref
(B). Records JS errors, body text length, scroll size, and a full-page screenshot per run.

Usage: ffcompare.py URLS.txt OUTDIR
Resumable: skips URLs already in OUTDIR/results.jsonl.
"""
import hashlib, json, os, sys, concurrent.futures as cf
from ff import Browser, scrub

PAGE_TIMEOUT = 90
MEASURE = """return {
  text: (document.body && document.body.innerText || '').length,
  w: document.documentElement.scrollWidth, h: document.documentElement.scrollHeight,
  forms: document.forms.length, imgs: document.images.length,
}"""


def run(url, block, shot):
    b = Browser(block=block)
    try:
        b.d.set_window_size(1366, 900)
        with cf.ThreadPoolExecutor(1) as ex:
            r = ex.submit(b.visit, url, 6).result(timeout=PAGE_TIMEOUT)
            m = ex.submit(b.d.execute_script, MEASURE).result(timeout=15)
            ex.submit(b.d.get_full_page_screenshot_as_file, shot).result(timeout=30)
        return {"load_error": r["load_error"], "errors": [e for k, e in r["events"] if k == "error"], **m}
    except Exception as ex:
        return {"load_error": type(ex).__name__}
    finally:
        b.quit()


def main():
    urls_file, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(os.path.join(outdir, "shots"), exist_ok=True)
    res = os.path.join(outdir, "results.jsonl")
    done = {json.loads(l)["url"] for l in open(res)} if os.path.exists(res) else set()
    for url in dict.fromkeys(l.strip() for l in open(urls_file)):
        if not url or url in done:
            continue
        h = hashlib.sha1(url.encode()).hexdigest()[:12]
        rec = {"url": url, "id": h}
        for label, block in [("A", False), ("A2", False), ("B", True)]:
            rec[label] = run(url, block, os.path.join(outdir, "shots", f"{h}-{label}.png"))
        with open(res, "a") as f:
            f.write(json.dumps(rec) + "\n")
        print(h, url, {k: (rec[k].get("load_error"), len(rec[k].get("errors", []))) for k in "A A2 B".split()}, flush=True)


if __name__ == "__main__":
    main()
