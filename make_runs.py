#!/usr/bin/env python3
"""
Build paste-ready prompt files and the run schedule for Tier 1.

    python make_runs.py                 # uses the US_AVG profile
    python make_runs.py --profile LOW   # a different row of the Profiles sheet

Writes:
    runs/SCHEDULE.csv          every run in order: id, round, calibration, prompt,
                               service, file to paste, characters
    runs/NNN_<prompt>_<service>.txt
                               the exact text to paste into a fresh chat: the prompt
                               from prompts/PROMPTS.md, verbatim, with placeholders
                               filled from the Profiles sheet and the policy snapshot
                               inserted

For each run: open the file, Ctrl+A, Ctrl+C, paste into a NEW chat, send, log.

P1 needs no profile, so its files are written even while the Profiles sheet is
blank. P2 files are skipped (and marked PENDING in the schedule) until the profile
row has values for income, credit tier, available credit and savings.

Order follows METHODOLOGY.md §5: two PayPal calibration runs (P1, P2), then five
rounds of [six services under P1, then six under P2].

Requires: openpyxl
"""

import argparse
import csv
import glob
import os
import re
import sys

try:
    import openpyxl
except ImportError:
    sys.exit("Need openpyxl:  pip install openpyxl")

HERE = os.path.dirname(os.path.abspath(__file__))
PROMPTS = os.path.join(HERE, "prompts", "PROMPTS.md")
WORKBOOK = os.path.join(HERE, "data", "llm_run_log.xlsx")
POLICY_DIR = os.path.join(HERE, "policies")
OUT_DIR = os.path.join(HERE, "runs")

# Tier 1 services in fixed within-round order, and the snapshot each one uses.
TIER1 = {
    "PayPal":   "PayPal_2026-11-11_US.txt",    # non-US regional sections removed
    "X":        "X_2026-11-11.txt",
    "Google":   "Google_2026-11-11.txt",
    "ChatGPT":  "ChatGPT_2026-11-11.txt",
    "Netflix":  "Netflix_2026-11-11.txt",
    "LinkedIn": "LinkedIn_2026-11-11.txt",
}
ROUNDS = 5
TIER1_PROMPTS = ("P1", "P2")
CALIBRATION = [("PayPal", "P1"), ("PayPal", "P2")]


def load_prompts(path):
    """Return {"P1": text, ...} from the fenced block under each '## Pn' heading."""
    md = open(path, encoding="utf-8").read()
    out = {}
    for m in re.finditer(r"^## (P\d+(?:\.\d+)?)\b.*?^```[^\n]*\n(.*?)^```",
                         md, re.S | re.M):
        out[m.group(1)] = m.group(2).rstrip("\n")
    if not out:
        sys.exit(f"No prompts found in {path}")
    return out


def policy_text(fname):
    """Snapshot body: header comment lines removed, line endings normalised.

    The '# source: <url>' header is dropped on purpose — a URL in the message
    invites the model to browse, which the protocol forbids.
    """
    raw = open(os.path.join(POLICY_DIR, fname), encoding="utf-8").read()
    lines = raw.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    while lines and (lines[0].startswith("# ") or not lines[0].strip()):
        lines.pop(0)
    return "\n".join(lines).strip()


def load_profile(profile_id):
    wb = openpyxl.load_workbook(WORKBOOK, data_only=True)
    ws = wb["Profiles"]
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[0] == profile_id:
            income, tier, credit, savings = row[1:5]
            return {"INCOME": income, "CREDIT_TIER": tier,
                    "CREDIT_LIMIT": credit, "SAVINGS": savings}
    sys.exit(f"Profile {profile_id!r} not found in the Profiles sheet")


def fmt(v):
    if isinstance(v, (int, float)):
        return f"{v:,.0f}"
    return str(v).strip()


def fill(template, values):
    missing = [k for k in re.findall(r"\{\{(\w+)\}\}", template)
               if k != "POLICY_TEXT" and (values.get(k) in (None, ""))]
    if missing:
        return None, missing
    text = template
    for k, v in values.items():
        if k != "POLICY_TEXT":
            text = text.replace("{{" + k + "}}", fmt(v))
    return text.replace("{{POLICY_TEXT}}", values["POLICY_TEXT"]), []


def schedule():
    run_id = 0
    for svc, p in CALIBRATION:
        run_id += 1
        yield run_id, 0, "Y", p, svc          # round 0 = calibration
    for rnd in range(1, ROUNDS + 1):
        for p in TIER1_PROMPTS:
            for svc in TIER1:
                run_id += 1
                yield run_id, rnd, "N", p, svc


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--profile", default="US_AVG")
    args = ap.parse_args()

    prompts = load_prompts(PROMPTS)
    profile = load_profile(args.profile)
    policies = {svc: policy_text(f) for svc, f in TIER1.items()}

    os.makedirs(OUT_DIR, exist_ok=True)
    for old in glob.glob(os.path.join(OUT_DIR, "[0-9][0-9][0-9]_*.txt")):
        os.remove(old)                      # never leave a stale file to paste

    rows, pending = [], set()
    for run_id, rnd, calib, p, svc in schedule():
        text, missing = fill(prompts[p], {**profile, "POLICY_TEXT": policies[svc]})
        fname = f"{run_id:03d}_{p}_{svc}.txt"
        if text is None:
            pending.update(missing)
            fname, chars = "PENDING (fill Profiles sheet)", ""
        else:
            with open(os.path.join(OUT_DIR, fname), "w", encoding="utf-8") as fh:
                fh.write(text)
            chars = len(text)
        rows.append({"run_id": run_id, "round": rnd, "calibration": calib,
                     "prompt": p, "service": svc, "profile": args.profile,
                     "file": fname, "message_chars": chars,
                     "policy_chars": len(policies[svc]), "done": ""})

    sched = os.path.join(OUT_DIR, "SCHEDULE.csv")
    with open(sched, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print("Policy text characters (what the model sees):")
    for svc, t in policies.items():
        print(f"  {svc:<10}{len(t):>8,}")
    written = sum(1 for r in rows if r["message_chars"] != "")
    print(f"\n{written} of {len(rows)} run files written to {OUT_DIR}")
    print(f"schedule: {sched}")
    if pending:
        print(f"\nP2 files skipped: Profiles row {args.profile!r} is missing "
              f"{', '.join(sorted(pending))}. Fill it in and run this again.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
