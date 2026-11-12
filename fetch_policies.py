#!/usr/bin/env python3
"""
Download and freeze privacy policy snapshots.

Run ONCE at the start of data collection, then use the saved files for every
LLM run. Policies change; a frozen copy is what makes the runs reproducible.

    python3 fetch_policies.py

Writes:
    policies/<service>_<YYYY-MM-DD>.txt   one plain-text snapshot per service
    policies/manifest.csv                 url, fetch time, status, char count

Requires: requests        (pip install requests)
Optional: beautifulsoup4  (pip install beautifulsoup4) for cleaner text;
          falls back to a regex strip if it is not installed.
"""

import csv
import os
import re
import sys
import time
from datetime import date, datetime, timezone

try:
    import requests
except ImportError:
    sys.exit("Need requests:  pip install requests")

try:
    from bs4 import BeautifulSoup
    HAVE_BS4 = True
except ImportError:
    HAVE_BS4 = False

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "policies")

# Privacy / cookie document URLs, taken from the Policy URL column of
# privacy_claims_verification_2.xlsx.
#
# FLAGGED entries are known to be the wrong document or an unusual variant.
# Fix the URL before collecting, or record the mismatch as a limitation.
POLICIES = {
    "Adobe":      "https://www.adobe.com/privacy/policy.html",
    "Airbnb":     "https://www.airbnb.com/terms/privacy_policy",
    "Canvas":     "https://www.instructure.com/policies/marketing-privacy",   # FLAGGED: marketing policy, not the Canvas LMS product policy
    "ChatGPT":    "https://openai.com/policies/privacy-policy",
    "Google":     "https://policies.google.com/privacy",
    "LinkedIn":   "https://www.linkedin.com/legal/privacy-policy",
    "McDonalds":  "https://www.mcdonalds.com/us/en-us/privacy.html",
    "Meta":       "https://mbasic.facebook.com/privacy/policy/printable/version/25862970456621906/",  # FLAGGED: version-pinned mbasic printable
    "Netflix":    "https://help.netflix.com/legal/privacy",
    "PayPal":     "https://www.paypal.com/us/webapps/mpp/ua/privacy-full",
    "Shopify":    "https://www.shopify.com/legal/cookies",                    # FLAGGED: cookie policy, not the main privacy policy
    "Uber":       "https://privacy.uber.com/",
    "X":          "https://x.com/en/privacy",
}

# Excluded: Claude, Truist, Epic Systems — no usable privacy-document claims
# in the ToS;DR dataset, so there is nothing to compare an estimate against.

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def to_text(html: str) -> str:
    if HAVE_BS4:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript", "svg", "nav", "footer"]):
            tag.decompose()
        text = soup.get_text("\n")
    else:
        text = re.sub(r"(?is)<(script|style|noscript|svg).*?</\1>", " ", html)
        text = re.sub(r"(?s)<[^>]+>", "\n", text)
        text = (text.replace("&nbsp;", " ").replace("&amp;", "&")
                    .replace("&lt;", "<").replace("&gt;", ">")
                    .replace("&quot;", '"').replace("&#39;", "'"))
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip()


def main() -> int:
    os.makedirs(OUT_DIR, exist_ok=True)
    stamp = date.today().isoformat()
    rows, failures = [], 0

    if not HAVE_BS4:
        print("note: beautifulsoup4 not installed, using regex fallback\n")

    for service, url in sorted(POLICIES.items()):
        fetched = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=30)
            status, text = r.status_code, to_text(r.text)
        except Exception as exc:                      # noqa: BLE001
            status, text = f"ERROR {type(exc).__name__}", ""

        ok = (status == 200 and len(text) > 2000)
        if not ok:
            failures += 1

        path = ""
        if text:
            path = os.path.join(OUT_DIR, f"{service}_{stamp}.txt")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(f"# {service}\n# source: {url}\n# fetched: {fetched}\n\n{text}")

        rows.append({
            "service": service, "url": url, "fetched_utc": fetched,
            "http_status": status, "chars": len(text),
            "file": os.path.basename(path), "looks_ok": "Y" if ok else "CHECK",
        })
        print(f"{service:<11} {str(status):<16} {len(text):>7} chars  {'ok' if ok else 'CHECK THIS'}")
        time.sleep(1.5)

    man = os.path.join(OUT_DIR, "manifest.csv")
    with open(man, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"\nmanifest: {man}")
    if failures:
        print(f"\n{failures} need checking. A short page usually means the policy is "
              f"rendered by JavaScript — open it in a browser, select all, and save "
              f"the text by hand to policies/<Service>_{stamp}.txt, then set "
              f"looks_ok to Y in the manifest.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
