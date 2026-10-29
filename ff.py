"""Firefox Nightly driver: pref on (`block`, the proposed behavior) or off (today's behavior),
optionally with the detection preload script (`preload.js`)."""
import json, os, re, time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

from props import CATEGORY

FIREFOX = "/Applications/Firefox Nightly.app/Contents/MacOS/firefox"
GECKODRIVER = os.path.expanduser("~/git/web-platform-tests/wpt/_venv3/bin/geckodriver")
HERE = os.path.dirname(os.path.abspath(__file__))
PRELOAD = "\n".join(l for l in open(os.path.join(HERE, "preload.js")).read().split("\n")
                    if not l.startswith("//"))
PRELOAD_DECL = "() => { (%s)(%s); }" % (PRELOAD.strip(), json.dumps(sorted(CATEGORY)))


COUNTRY_HOST = re.compile(r"\b((?:google|bing|yahoo|amazon|facebook)\.)(?:co\.)?(?!com\b|net\b|org\b)[a-z]{2}\b")


def scrub(s):
    """Strip URL queries and fragments (any scheme) and mask country-specific hosts."""
    s = re.sub(r"(\b[a-z][a-z0-9+.-]*://[^\s?#\"'<>]*)[?#][^\s\"'<>:]*", r"\1", s or "")
    return COUNTRY_HOST.sub(r"\1<cc>", s)


class Browser:
    def __init__(self, block, preload=False, headless=True):
        o = Options()
        o.binary_location = FIREFOX
        if headless:
            o.add_argument("-headless")
        o.enable_bidi = True
        o.set_preference("dom.document.name_getter_prevent_shadowing.enabled", block)
        o.set_preference("dom.disable_open_during_load", True)
        o.set_preference("media.autoplay.default", 5)
        self.d = webdriver.Firefox(options=o, service=Service(GECKODRIVER))
        self.d.set_page_load_timeout(30)
        self.d.set_script_timeout(10)
        self.events = []
        self.d.script.add_console_message_handler(self._console)
        self.d.script.add_javascript_error_handler(self._error)
        if preload:
            self.d.script.pin(PRELOAD_DECL)

    def _console(self, e):
        if e.text and e.text.startswith("__SHADOW__"):
            self.events.append(("shadow", json.loads(e.text[len("__SHADOW__"):])))
        elif e.text and e.text.startswith("RESULT "):
            self.events.append(("result", json.loads(e.text[len("RESULT "):])))

    def _error(self, e):
        self.events.append(("error", scrub(e.text)[:300]))

    def visit(self, url, settle=5):
        self.events = []
        err = None
        try:
            self.d.get(url)
        except Exception as ex:  # page load timeout etc.; keep what we have
            err = type(ex).__name__
        time.sleep(settle)
        return {"load_error": err, "events": list(self.events)}

    def quit(self):
        try:
            self.d.quit()
        except Exception:
            pass
