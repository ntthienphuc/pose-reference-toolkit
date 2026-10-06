"""Real browser check against a running local demo server; Playwright is dev-only."""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument("--url", default="http://127.0.0.1:8010")
parser.add_argument("--out", required=True)
args = parser.parse_args()
errors, cases = [], []
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width":1100,"height":850})
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(args.url)
    page.wait_for_function("document.querySelector('#status').textContent === 'Ready'")
    for name, expected in (("same","match"),("wrong","low_similarity"),("missing","needs_recapture"),("degenerate","needs_recapture")):
        page.locator('[data-demo="'+name+'"]').click()
        page.wait_for_function("!document.querySelector('[data-demo=same]').disabled")
        status = page.locator("#status").inner_text()
        assert status.startswith(expected), (name, status)
        cases.append({"name":name,"status":status})
    page.locator('[data-demo="same"]').click()
    page.wait_for_function("!document.querySelector('[data-demo=same]').disabled")
    page.locator("#frame").fill("12")
    assert "Step 13/32" in page.locator("#alignment").inner_text()
    page.set_viewport_size({"width":390,"height":844})
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(Path(args.out).with_suffix(".png")), full_page=True)
    browser.close()
assert not errors, errors
Path(args.out).write_text(json.dumps({"status":"passed","cases":cases,"mobile_overflow":False,"page_errors":errors},indent=2)+"\n",encoding="utf-8")
print("Browser checks passed: 4 outcomes, alignment slider, mobile layout, no page errors")
