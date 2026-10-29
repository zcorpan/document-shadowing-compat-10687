"""Scan Common Crawl WARCs for named elements (per the Document named getter's filter) whose name
shadows a property on `document`'s prototype chain, and for inline-script references to
`document.<name>`.

Usage: scan.py OUT.jsonl WARC...
"""
import json, multiprocessing as mp, re, sys

from props import CATEGORY, kind
from cc import html_responses

NAMES = sorted(CATEGORY, key=len, reverse=True)
NAME_ALT = "|".join(map(re.escape, NAMES))
PREFILTER = re.compile(r"""\b(?i:name|id)\s*=\s*["']?\s*(?:%s)\s*["'\s/>]""" % NAME_ALT)


def named_elements(tree):
    """(element, attribute, value) for named elements per the HTML Standard's Document named
    getter filter (ignoring the "exposed" condition for embed/object)."""
    out = []
    for el in tree.css("embed[name], form[name], iframe[name], img[name], object[name]"):
        v = el.attributes.get("name")
        if v:
            out.append((el.tag, "name", v))
    for el in tree.css("object[id], img[id][name]"):
        if el.tag == "img" and not el.attributes.get("name"):
            continue
        v = el.attributes.get("id")
        if v:
            out.append((el.tag, "id", v))
    return out


def scan_page(args):
    url, html = args
    from selectolax.lexbor import LexborHTMLParser
    tree = LexborHTMLParser(html)
    hits = [(t, a, v) for t, a, v in named_elements(tree) if v in CATEGORY]
    if not hits:
        return None
    scripts = "\n".join(s.text() or "" for s in tree.css("script:not([src])"))
    names = sorted({v for _, _, v in hits})
    refs = {}
    for n in names:
        pat = re.compile(r"""\bdocument\s*(?:\.\s*%s\b|\[\s*["']%s["']\s*\])""" % (re.escape(n), re.escape(n)))
        m = pat.search(scripts)
        if m:
            refs[n] = scripts[max(0, m.start() - 80):m.end() + 80]
    ends = bool(re.search(r"</(?:body|html)>\s*$", html[-2000:], re.I))
    return {
        "url": url,
        "elements": [{"tag": t, "attr": a, "name": v, "category": CATEGORY[v], "kind": kind(v)} for t, a, v in hits],
        "inline_refs": refs,
        "complete": ends,
    }


def candidates(warcs, counter):
    for w in warcs:
        for url, html in html_responses(w):
            counter[0] += 1
            if PREFILTER.search(html):
                counter[1] += 1
                yield url, html


def main():
    out, warcs = sys.argv[1], sys.argv[2:]
    counter = [0, 0]
    n_hits = 0
    with mp.Pool(8) as pool, open(out, "w") as f:
        for r in pool.imap_unordered(scan_page, candidates(warcs, counter), chunksize=16):
            if r:
                n_hits += 1
                f.write(json.dumps(r) + "\n")
    json.dump({"pages": counter[0], "prefiltered": counter[1], "hits": n_hits},
              open(out + ".totals.json", "w"), indent=1)
    print(counter, n_hits)


if __name__ == "__main__":
    main()
