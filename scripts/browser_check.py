"""Exercise real HTTP, WebSocket and React rendering in a local browser."""

import json
import os
from pathlib import Path

import numpy as np
from playwright.sync_api import sync_playwright

out = Path("docs/results")
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH"))
    context = browser.new_context(viewport={"width": 1440, "height": 1000})
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto("http://127.0.0.1:8000")
    page.get_by_label("Operator password").fill(os.environ["MERIDIAN_PASSWORD"])
    page.get_by_role("button", name="Open console").click()
    page.get_by_role("heading", name="Signal overview.").wait_for()
    page.add_init_script(
        """(() => {window.arrival=[];const Native=window.WebSocket;window.WebSocket=class extends Native {constructor(...args){super(...args);this.addEventListener('message', e=>{const p=JSON.parse(e.data);if(p.captured_at)window.arrival.push({capture:p.captured_at,arrival:Date.now()/1000,seq:p.seq,samples:p.samples_total});});}};})()"""
    )
    # Reload reconnects through the instrumentation while preserving the authenticated cookie.
    page.reload()
    page.get_by_role("button", name="Start live run").click()
    page.wait_for_function("window.arrival.length >= 100", timeout=15000)
    page.get_by_role("button", name="Stop", exact=True).click()
    page.wait_for_timeout(300)
    page.get_by_role("button", name="Verify replay").first.click()
    page.get_by_role("status").filter(has_text="Bit-identical").wait_for()
    page.get_by_role("button", name="Measure synthetic batch").click()
    page.get_by_text("93.7%").wait_for()
    page.screenshot(path=str(out / "console-desktop.png"), full_page=True)
    raw = page.evaluate("window.arrival")
    latencies = [(x["arrival"] - x["capture"]) * 1000 for x in raw]
    desktop_overflow = page.evaluate("document.documentElement.scrollWidth>innerWidth")
    page.set_viewport_size({"width": 390, "height": 844})
    page.screenshot(path=str(out / "console-mobile.png"), full_page=True)
    mobile_overflow = page.evaluate("document.documentElement.scrollWidth>innerWidth")
    assert not errors and not desktop_overflow and not mobile_overflow
    result = {
        "frames": len(raw),
        "latency_p50_ms": float(np.quantile(latencies, 0.5)),
        "latency_p99_ms": float(np.quantile(latencies, 0.99)),
        "boundary": "synthetic batch capture through local WebSocket browser message event; excludes paint; same machine wall clock",
        "configured_streams": 3,
        "configured_ticks_per_second": 50,
        "configured_source_rates_hz": [50, 25, 50 / 3],
        "observed_samples_per_second": (raw[-1]["samples"] - raw[0]["samples"])
        / (raw[-1]["capture"] - raw[0]["capture"]),
        "dropout": 0.1,
        "page_errors": errors,
        "desktop_overflow": desktop_overflow,
        "mobile_overflow": mobile_overflow,
        "verified_actions": [
            "login",
            "live frames",
            "stop",
            "persisted replay",
            "station batch",
            "mobile layout",
        ],
    }
    (out / "browser-samples.json").write_text(json.dumps(raw, indent=2) + "\n")
    (out / "browser.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    browser.close()
