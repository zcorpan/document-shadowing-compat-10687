"""Check that Firefox Nightly's DocumentShadowingBlockedWarning reaches WebDriver BiDi log events,
and that the pref toggles the behavior."""
import os, sys, time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

FIREFOX = "/Applications/Firefox Nightly.app/Contents/MacOS/firefox"
GECKODRIVER = os.path.expanduser("~/git/web-platform-tests/wpt/_venv3/bin/geckodriver")
PAGE = ("data:text/html,<!DOCTYPE html><form name=createElement></form><form name=title></form>"
        "<script>document.createElement;document.title;</script>")


def run(block):
    o = Options()
    o.binary_location = FIREFOX
    o.add_argument("-headless")
    o.enable_bidi = True
    o.set_preference("dom.document.name_getter_prevent_shadowing.enabled", block)
    d = webdriver.Firefox(options=o, service=Service(GECKODRIVER))
    seen = []
    d.script.add_console_message_handler(lambda e: seen.append(("console", e.level, e.text)))
    d.script.add_javascript_error_handler(lambda e: seen.append(("js", e.level, e.text)))
    d.get(PAGE)
    time.sleep(1)
    r = d.execute_script("return [String(document.createElement).slice(0,30), String(document.title)]")
    time.sleep(1)
    d.quit()
    print(block, r, seen)


run(True)
run(False)
