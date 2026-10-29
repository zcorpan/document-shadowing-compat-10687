// Preload script (all frames, document start). Own properties on `document` win over named
// properties, so an own accessor per prototype-chain name sees every get and set and returns what
// the prototype chain gives (the proposed behavior). Logs each access made while a named element
// (per the HTML Standard's Document named getter filter) with that name exists.
(names) => {
  const dbg = console.debug.bind(console);
  const proto = Object.getPrototypeOf(document);
  const byName = Document.prototype.getElementsByName;
  const byId = Document.prototype.getElementById;
  const qsa = Document.prototype.querySelectorAll;
  const esc = CSS.escape;
  const NAMED = new Set(["embed", "form", "iframe", "img", "object"]);
  const HTML = "http://www.w3.org/1999/xhtml";
  const seen = new Set();
  const named = (name) => {
    if (byId.call(document, name) === null && byName.call(document, name).length === 0) return null;
    const out = [];
    for (const el of byName.call(document, name))
      if (el.namespaceURI === HTML && NAMED.has(el.localName)) out.push(el);
    const n = esc(name);
    for (const el of qsa.call(document, `object[id="${n}"], img[id="${n}"][name]:not([name=""])`))
      if (el.namespaceURI === HTML && !out.includes(el)) out.push(el);
    return out.length ? out : null;
  };
  const stack = () => new Error().stack.split("\n")
    .filter(l => l && !l.includes("__shadowPreload")).slice(0, 4).join("\n");
  const report = (op, name, els) => {
    const st = stack();
    const key = op + name + st;
    if (seen.has(key)) return;
    seen.add(key);
    dbg("__SHADOW__" + JSON.stringify({
      op, name, count: els.length, tags: els.slice(0, 3).map(e => e.localName),
      attr: els[0].getAttribute("name") === name ? "name" : "id",
      stack: st, frame: location.origin, readyState: document.readyState,
    }));
  };
  const findDesc = (name) => {
    let p = proto, d;
    while (p && !(d = Object.getOwnPropertyDescriptor(p, name))) p = Object.getPrototypeOf(p);
    return d;
  };
  for (const name of names) {
    if (Object.getOwnPropertyDescriptor(document, name)) continue; // e.g. location
    Object.defineProperty(document, name, {
      configurable: true,
      enumerable: false,
      get: function __shadowPreloadGet() {
        const els = named(name);
        if (els) report("get", name, els);
        return Reflect.get(proto, name, document);
      },
      set: function __shadowPreloadSet(val) {
        const els = named(name);
        if (els) report("set", name, els);
        const d = findDesc(name);
        if (d && d.set) d.set.call(document, val);
        else if (!d || d.writable)
          Object.defineProperty(document, name, {value: val, writable: true, enumerable: true, configurable: true});
      },
    });
  }
}
