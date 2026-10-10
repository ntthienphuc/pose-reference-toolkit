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
    assert page.locator("#download").is_disabled(), "No receipt exists before comparison"
    downloaded_queries = []
    for name, expected in (("same","match"),("wrong","low_similarity"),("missing","needs_recapture"),("degenerate","needs_recapture")):
        with page.expect_response(lambda response: response.url.endswith("/compare") and response.request.method == "POST") as response_info:
            page.locator('[data-demo="'+name+'"]').click()
        full_result = response_info.value.json()
        page.wait_for_function("!document.querySelector('[data-demo=same]').disabled")
        status = page.locator("#status").inner_text()
        assert status.startswith(expected), (name, status)
        assert page.locator("#download").is_enabled()
        with page.expect_download() as download_info:
            page.locator("#download").click()
        download = download_info.value
        assert download.suggested_filename == "pose-reference-receipt.json"
        downloaded = json.loads(Path(download.path()).read_text(encoding="utf-8"))
        assert downloaded == full_result, "Downloaded receipt must preserve the complete server result"
        visible = json.loads(page.locator("#receipt").inner_text())
        expected_visible = dict(downloaded)
        if downloaded.get("feedback"):
            expected_visible["feedback"] = "Shown above"
            assert downloaded["feedback"]["reference_xy"] and downloaded["alignment_pairs"]
            assert downloaded["matched_reference_id"] and downloaded["policy"]
        assert visible == expected_visible, "Download and current displayed case differ"
        downloaded_queries.append(downloaded["query_pose_sha256"])
        cases.append({"name":name,"status":status,"full_receipt_download":"passed"})
    assert len(set(downloaded_queries)) == 4, "Each comparison must replace the previous receipt"
    # A failed new upload must not offer the previous comparison as its receipt.
    page.locator("#upload").click()
    page.wait_for_function("!document.querySelector('[data-demo=same]').disabled")
    with page.expect_download() as failed_download_info:
        page.locator("#download").click()
    failed_receipt = json.loads(Path(failed_download_info.value.path()).read_text(encoding="utf-8"))
    assert failed_receipt == {"status":"reject","score":None,"reasons":["Choose a pose JSON or video clip"]}
    assert failed_receipt == json.loads(page.locator("#receipt").inner_text())
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
Path(args.out).write_text(json.dumps({"status":"passed","cases":cases,"receipt_disabled_before_result":True,"failed_request_replaces_receipt":True,"mobile_overflow":False,"page_errors":errors},indent=2)+"\n",encoding="utf-8")
print("Browser checks passed: 4 outcomes and full JSON downloads, no stale failed-request receipt, alignment slider, mobile layout, no page errors")
