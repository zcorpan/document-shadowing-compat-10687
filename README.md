# Compat impact of not letting named elements shadow `document`'s prototype chain (whatwg/html#10687)

Today `Document` has `[LegacyOverrideBuiltIns]`, so `<form name=createElement>` makes
`document.createElement` return the form, and the same goes for every property on `document`'s
prototype chain (`Document`, `Node`, `EventTarget`, `Object.prototype`). The proposal: named
elements never shadow those properties. The goal is the security property: markup injected into a
page can't replace `document.currentScript`, `document.cookie`, `document.createElement`, … as
seen by the page's scripts.

Firefox Nightly has implemented this since Firefox 143
(`dom.document.name_getter_prevent_shadowing.enabled`, on in Nightly only): every Web IDL member of
`HTMLDocument` and its ancestors (attributes, methods, event handlers, constants) plus the
`Object.prototype` names. All numbers below come from files in this repo; `summarize.py` recomputes
them into `data/summary.json`.

## Summary

- Names other than `Document` attributes basically don't get shadowed in practice. Across 294 HTTP
  Archive pages that hit Chrome's counter and 24 Common Crawl pages with a shadowing named element,
  the only such name accessed on load was `when` (3 pages): a method only Chrome has, from the
  Observable API on `EventTarget.prototype`. No `Document` methods, `Node` members or
  `Object.prototype` names were accessed.
- Those 3 `when` pages rely on the shadowing (`document.when.month.selectedIndex = …` with
  `<form name=when>`, from an old calendar script). They keep working in Firefox and Safari, which
  don't have `when`. Chrome would break them if blocking covers its whole prototype chain.
- Before/after in Firefox Nightly 161 on the 147 pages that accessed a shadowed name: 0 got worse.
  2 visibly improved, 6 lost a script error with no visible change, and 8 more flagged pages were
  noise or measurement artifacts.

## 1. Use counter and HTTP Archive

Chrome's `DOMClobberedShadowedDocumentPropertyAccessed` (4872) fires when the `document` named
getter returns an element for a name that `GetRealNamedPropertyInPrototypeChain` also finds. That
covers the whole prototype chain, including `Object.prototype` and properties scripts add to the
prototypes
([`local_window_proxy.cc`](https://chromium.googlesource.com/chromium/src/+/6ca4e60b94475/third_party/blink/renderer/bindings/core/v8/local_window_proxy.cc#606)).
On chromestatus it averaged about 0.002% of page loads per month from 2025-09 to 2026-10.

`queries/4872-pages.sql` (2026-10-01 crawl, root pages, 114 GB processed) returns 268 desktop and
196 mobile pages that hit 4872 (out of 11,650,352 and 15,366,242 root pages), 294 distinct URLs.

## 2. Common Crawl

`scan.py` looked at 255,716 HTML responses in 12 WARCs from CC-MAIN-2026-39 for named elements
(per the HTML Standard's named getter filter: `embed`/`form`/`iframe`/`img`/`object` with `name`,
`object` with `id`, `img` with `id` and a non-empty `name`) whose name is on `document`'s prototype
chain in Chrome Canary 158, Firefox Nightly 161 or Safari TP (`props.py`). 24 pages have one: 23
with `Document` attribute names (`links`, `domain`, `cookie`, `forms`, `fonts`, `body`, `title`), 1
with a method name (`<form name=write>` on a zboard page, whose submit handler gets the form via
`this`). None of the 24 has an inline script reading `document.<name>`.

## 3. Detection on live pages

`preload.js` (a WebDriver BiDi preload script, Firefox Nightly with the pref off) defines an own
accessor on `document` for every name in `props.py`. Own properties take priority over named
properties, so the accessor sees every get and set; it logs those made while a matching named
element exists and returns the prototype's value. `test/preload-test.html` checks it against the
pref: same results in the top-level document. The preload didn't run in child frames, so detection
covers top-level documents only.

`detect.py` loaded the 294 HTTP Archive URLs (31 hit the 30 s load timeout; events up to then are
recorded) and the 24 Common Crawl URLs:

| Name | Pages (HTTP Archive) | Main callers |
|---|---|---|
| `hidden` | 57 | gtag.js, jQuery 3.5.1, Yandex Metrica, Bootstrap |
| `cookie` | 47 | Matomo, gtag.js, GTM, Cookiebot, analytics.js |
| `title` | 16 | analytics.js, gtag.js, ga.js |
| `scripts` | 11 | gtm.js |
| `body` | 5 | jQuery, jstree, ad scripts |
| `head` | 5 | jQuery, Font Awesome, wp-emoji, widgets |
| `when` | 3 | same-site calendar script (relies on getting the form) |
| `all`, `forms`, `domain`, `images`, `links` | 2 each | fbevents.js, ga.js, Dreamweaver `MM_*` helpers, old sniffing |

Common Crawl pages: `domain` (3) and `cookie` (2), 2 load errors. Nearly all callers are libraries
that expect the real property.

## 4. Before/after in Firefox Nightly

`ffcompare.py` loaded each of the 147 pages that accessed a shadowed name (142 HTTP Archive, 5
Common Crawl) three times at 1366×900: pref off (A, A2) and pref on (B). It recorded JS errors,
text length, scroll size and a full-page screenshot. `ffanalyze.py` flagged 16 pages where B
differs from A beyond the A/A2 noise (`out/flags.json`). `review/` has an A|B image per flagged page
(A left, B right) and `review/ratings.csv` has the ratings:

| Rating | Pages |
|---|---|
| broken / worse | 0 |
| improved (visible) | 2 |
| no visible change | 14 (6 lose a script error, 8 noise or measurement artifacts) |

- zipperenzo.nl: today cookie code fails on `<form name=cookie>`, and the hero images and Google
  Translate widget don't load; with blocking they do
  ([review image](review/a4c882f7e2a4.jpg)).
- rajhlinky.wz.cz: today the host's floating ad script fails on `<iframe name=body>`; with blocking
  it renders ([review image](review/4d9092e1fa33.jpg)).

## Variants

- Drop `[LegacyOverrideBuiltIns]` from `Document` (Web IDL's default named property visibility):
  nothing on the prototype chain is shadowed, including members added later and properties scripts
  add. The simplest spec change. Each new member on `Document`, `Node`, `EventTarget` or
  `Object.prototype` then also stops pages that use that name for a form from finding it, as `when`
  shows (3 of 263 loaded counter pages in this sample).
- A fixed list (e.g. today's standard members): new members stay shadowable, so adding them stays as
  safe as today, but they aren't protected against clobbering.

Firefox's implementation is between the two: every Web IDL member at build time (so new members
are covered as they ship), but not script-added properties.

## Not covered

- Accesses after load or on interaction (form submission, clicks), and child frames for detection.
- Pages that use the Chrome-only `when` were measured in Firefox, which doesn't have it; their
  breakage is inferred from their code.
- Firefox's per-name telemetry for all properties (Firefox 143 until its removal in 2026-09) isn't
  public.

## Reproduce

```sh
python3 -m venv .venv && .venv/bin/pip install warcio selectolax selenium pillow
bq query --use_legacy_sql=false --format=csv --max_rows=100000 < queries/4872-pages.sql > queries/4872-pages.csv
.venv/bin/python scan.py data/cc-hits.jsonl ~/git/commoncrawl/cc-data/CC-MAIN-2026-39/*.warc.gz
.venv/bin/python test/run_preload_test.py
.venv/bin/python detect.py data/httparchive-urls.txt data/detect-httparchive.jsonl 4
.venv/bin/python detect.py data/cc-urls.txt data/detect-cc.jsonl 4
.venv/bin/python ffcompare.py data/compare-urls-0.txt out   # and -1, -2, -3
.venv/bin/python ffanalyze.py out > out/flags.json
python3 summarize.py
```

`data/cc-hits-v1.jsonl` is an earlier scan whose prefilter matched lowercase attribute names only;
the final scan found the same 24 pages. `ff_probe.py` showed that Firefox's "shadowing blocked"
console warning doesn't reach WebDriver BiDi, which is why detection uses the preload.
