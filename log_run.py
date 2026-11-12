#!/usr/bin/env python3
"""
Semi-automated run helper: puts each prompt on the clipboard and logs the answer.

    python log_run.py              # start at the next unlogged run
    python log_run.py --status     # show progress and exit
    python log_run.py --run 7      # do one specific run (e.g. to fill a gap)

Per run:
    1. The script copies the run's prompt to your clipboard.
    2. Open a NEW chat (Temporary Chat), Ctrl+V, Enter. Wait for the full answer.
    3. Click ChatGPT's copy button under the answer, come back here, press Enter.
    4. The script reads the answer from the clipboard, pulls out the numbers
       (P2: from the five-line format; P1: you pick, using the decision rules),
       and writes the Run Log row itself.

The ChatGPT step stays manual on purpose — see METHODOLOGY.md §5. Nothing here
talks to ChatGPT.

CLOSE THE WORKBOOK IN EXCEL while this runs; it writes to data/llm_run_log.xlsx.
Every answer is also saved to data/responses/NNN.txt before the workbook is
touched, so nothing is lost if a save fails.

Requires: openpyxl. Clipboard: PowerShell on Windows (built in); pbcopy on macOS;
xclip / wl-clipboard on Linux. With --no-clipboard you open the run file yourself
and paste the answer into the terminal instead.
"""

import argparse
import csv
import datetime as dt
import os
import re
import shutil
import subprocess
import sys

try:
    import openpyxl
except ImportError:
    sys.exit("Need openpyxl:  pip install openpyxl")

HERE = os.path.dirname(os.path.abspath(__file__))
WORKBOOK = os.path.join(HERE, "data", "llm_run_log.xlsx")
SCHEDULE = os.path.join(HERE, "runs", "SCHEDULE.csv")
RUNS_DIR = os.path.join(HERE, "runs")
RESP_DIR = os.path.join(HERE, "data", "responses")
EXCEL_CELL_MAX = 32767

# Run Log columns (1-based)
COL = dict(run_id=1, date=2, model=3, prompt=4, service=5, profile=6, usd=7, low=8,
           high=9, refused=10, truncated=11, top=12, raw=13, notes=14, round=15, calib=16)


# ---------------------------------------------------------------- clipboard
def _run(cmd, data=None):
    return subprocess.run(cmd, input=data, capture_output=True, check=True)


def clip_set(text):
    if os.name == "nt":
        tmp = os.path.join(RUNS_DIR, ".clip.tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(text)
        try:
            _run(["powershell", "-NoProfile", "-Command",
                  f"Get-Content -LiteralPath '{tmp}' -Raw -Encoding UTF8 | Set-Clipboard"])
        finally:
            os.remove(tmp)
        return
    for cmd in (["pbcopy"], ["wl-copy"], ["xclip", "-selection", "clipboard"]):
        if shutil.which(cmd[0]):
            _run(cmd, text.encode("utf-8"))
            return
    raise RuntimeError("no clipboard tool found")


def clip_get():
    if os.name == "nt":
        out = _run(["powershell", "-NoProfile", "-Command",
                    "[Console]::OutputEncoding=[Text.Encoding]::UTF8; Get-Clipboard -Raw"]).stdout
        return out.decode("utf-8", "replace").replace("\r\n", "\n").strip()
    for cmd in (["pbpaste"], ["wl-paste", "--no-newline"], ["xclip", "-selection", "clipboard", "-o"]):
        if shutil.which(cmd[0]):
            return _run(cmd).stdout.decode("utf-8", "replace").strip()
    raise RuntimeError("no clipboard tool found")


def paste_from_terminal():
    print("Paste the answer below, then type END on its own line and press Enter:")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "END":
            break
        lines.append(line)
    return "\n".join(lines).strip()


# ---------------------------------------------------------------- parsing
NUM = r"\$?\s*(-?\d[\d,]*(?:\.\d+)?)\s*(k|K|thousand|m|M|million)?\b"


def to_number(s, suffix=None):
    v = float(s.replace(",", ""))
    if suffix:
        v *= 1_000_000 if suffix.lower() in ("m", "million") else 1_000
    return round(v, 2) if v != int(v) else int(v)


def parse_p2(text):
    """Pull the five labelled lines out of a P2 answer. Missing fields -> None."""
    out = {}
    for key, field in (("ANNUAL_RISK_USD", "usd"), ("LOW_USD", "low"), ("HIGH_USD", "high")):
        m = re.search(rf"{key}[\s*_`]*[:=][\s*_`]*{NUM}", text, re.I)
        out[field] = to_number(m.group(1), m.group(2)) if m else None
    m = re.search(r"TOP_DATA_TYPES[\s*_`]*[:=][\s*_`]*(.+)", text, re.I)
    out["top"] = m.group(1).strip().strip("*`_ ").strip() if m else None
    return out


def dollar_mentions(text, limit=12):
    """Dollar amounts in the text, with a little context, for the P1 picker."""
    found = []
    for m in re.finditer(r"\$\s?\d[\d,]*(?:\.\d+)?(?:\s?(?:k|K|thousand|million|M)\b)?"
                         r"(?:\s?(?:-|–|to)\s?\$?\s?\d[\d,]*(?:\.\d+)?(?:\s?(?:k|K|thousand|million|M)\b)?)?",
                         text):
        a, b = max(0, m.start() - 50), min(len(text), m.end() + 50)
        ctx = " ".join(text[a:b].split())
        found.append((m.group(0), ctx))
        if len(found) >= limit:
            break
    return found


# ---------------------------------------------------------------- input helpers
def ask(prompt, default=None):
    d = f" [{default}]" if default not in (None, "") else ""
    try:
        v = input(f"{prompt}{d}: ").strip()
    except EOFError:
        sys.exit("\nInput ended — stopping. Nothing for the current run was written.")
    return v if v else (default if default is not None else "")


def ask_number(prompt, default=None):
    while True:
        v = ask(prompt, "" if default is None else default)
        if v in ("", None):
            return None
        m = re.fullmatch(NUM, str(v).strip())
        if m:
            return to_number(m.group(1), m.group(2))
        print("  Type a number like 1200 or $1,200 (or leave blank).")


# ---------------------------------------------------------------- workbook
def load_schedule():
    if not os.path.exists(SCHEDULE):
        sys.exit("No runs/SCHEDULE.csv — run  python make_runs.py  first.")
    with open(SCHEDULE, encoding="utf-8") as fh:
        return [r for r in csv.DictReader(fh)]


def logged(ws):
    """{run_id: row_number} for rows already in the Run Log, and the next free row."""
    done, last = {}, 1
    for r in range(2, ws.max_row + 1):
        vals = [ws.cell(r, c).value for c in (COL["run_id"], COL["prompt"], COL["service"])]
        if any(v not in (None, "") for v in vals):
            last = r
            try:
                done[int(vals[0])] = r
            except (TypeError, ValueError):
                pass
    return done, last + 1


def last_model(ws):
    for r in range(ws.max_row, 1, -1):
        v = ws.cell(r, COL["model"]).value
        if v:
            return str(v)
    return None


def check_writable(path):
    try:
        with open(path, "a+b"):
            pass
    except PermissionError:
        sys.exit("The workbook is open in Excel (or locked). Close it and run this again.")


def save_with_retry(wb, path):
    while True:
        try:
            wb.save(path)
            return
        except PermissionError:
            input("Can't save — the workbook is open in Excel. Close it, then press Enter to retry.")


# ---------------------------------------------------------------- one run
def do_run(run, model, args):
    rid = int(run["run_id"])
    fname = run["file"]
    path = os.path.join(RUNS_DIR, fname)
    if not os.path.exists(path):
        print(f"\nRun {rid} ({run['prompt']} {run['service']}) has no file yet: {fname}")
        print("Fill the Profiles sheet, close Excel, run  python make_runs.py, then try again.")
        return None
    prompt_text = open(path, encoding="utf-8").read()
    calib = run["calibration"] == "Y"

    print("\n" + "=" * 64)
    print(f" Run {rid} of 62   {run['prompt']}  {run['service']}   "
          + ("CALIBRATION (not scored)" if calib else f"round {run['round']}"))
    print("=" * 64)

    use_clip = not args.no_clipboard
    if use_clip:
        try:
            clip_set(prompt_text)
            print(f"Prompt is on your clipboard ({len(prompt_text):,} characters).")
        except Exception as exc:            # noqa: BLE001
            print(f"(Couldn't use the clipboard: {exc}. Falling back to manual.)")
            use_clip = False
    if not use_clip:
        print(f"Open {path}, Ctrl+A, Ctrl+C.")
    print("  1. NEW chat (Temporary Chat). Ctrl+V. Enter.")
    print("  2. Wait for the whole answer. Don't regenerate or reply.")

    while True:
        if use_clip:
            input("  3. Click ChatGPT's copy button under the answer, then press Enter here.")
            try:
                answer = clip_get()
            except Exception as exc:        # noqa: BLE001
                print(f"(Couldn't read the clipboard: {exc})")
                answer = paste_from_terminal()
        else:
            answer = paste_from_terminal()
        if not answer:
            print("  The clipboard is empty — copy the answer and try again.")
        elif answer.strip()[:300] == prompt_text.strip()[:300]:
            print("  That's still the prompt, not the answer — copy ChatGPT's reply and try again.")
        else:
            break

    # save the raw answer first, so it survives anything that goes wrong later
    os.makedirs(RESP_DIR, exist_ok=True)
    with open(os.path.join(RESP_DIR, f"{rid:03d}_{run['prompt']}_{run['service']}.txt"),
              "w", encoding="utf-8") as fh:
        fh.write(answer)

    preview = answer if len(answer) <= 1500 else answer[:1500] + "\n  [...]"
    print("\n----- answer -----\n" + preview + "\n------------------")

    rec = {"usd": None, "low": None, "high": None, "top": None, "refused": "N", "notes": ""}
    parsed = parse_p2(answer) if run["prompt"] in ("P2", "P3") else {}
    if parsed.get("usd") is not None:
        print(f"\nRead from the answer:  annual {parsed['usd']}   low {parsed['low']}   "
              f"high {parsed['high']}\n  top data types: {parsed['top']}")
        if ask("Correct? Enter = yes, n = edit", "").lower() != "n":
            rec.update({k: parsed[k] for k in ("usd", "low", "high", "top")})
        else:
            parsed = {}
    if rec["usd"] is None:
        if run["prompt"] in ("P2", "P3"):
            print("\nThe five-line format wasn't followed; apply the decision rules by hand.")
            rec["notes"] = "format not followed"
        mentions = dollar_mentions(answer)
        if mentions:
            print("\nDollar amounts in the answer:")
            for i, (amt, ctx) in enumerate(mentions, 1):
                print(f"  {i:>2}. {amt:<18} …{ctx}…")
        else:
            print("\nNo dollar amounts found in the answer.")
        print("\nDecision rules: one figure -> that. Range only -> low/high + midpoint (note it).\n"
              "Scenarios -> 'most likely'/'typical', else the lowest (note it).\n"
              "Monthly x12 / lifetime -> annual (note it). No number at all -> R.")
        while True:
            v = str(ask("Annual Risk USD — a number, a range like 50-500 (range only, no\n"
                        "point estimate), or R = refused", "R" if not mentions else "")).strip()
            rng = re.fullmatch(rf"{NUM}\s*(?:-|–|to)\s*{NUM}", v)
            one = re.fullmatch(NUM, v)
            if v.upper() == "R":
                rec["refused"] = "Y"
                break
            if rng:
                lo, hi = to_number(rng.group(1), rng.group(2)), to_number(rng.group(3), rng.group(4))
                rec.update(low=lo, high=hi, usd=(lo + hi) / 2)
                rec["notes"] = "; ".join(x for x in (rec["notes"], "midpoint") if x)
                print(f"  -> low {lo}, high {hi}, annual = midpoint {rec['usd']}")
                break
            if one:
                rec["usd"] = to_number(one.group(1), one.group(2))
                rec["low"] = ask_number("Low USD (blank if the answer gives none)")
                rec["high"] = ask_number("High USD (blank if the answer gives none)")
                break
            print("  Didn't understand that — try e.g. 1200, $1,200, 2.5k, 50-500 or R.")
        if rec["refused"] == "N" and run["prompt"] in ("P2", "P3"):
            rec["top"] = ask("Top data types (blank if none)", parsed.get("top") or "") or None
    note = ask("Notes (e.g. midpoint, converted from monthly, searched; Enter = none)",
               rec["notes"])
    rec["notes"] = note
    return {
        "run_id": rid, "date": dt.date.today().isoformat(), "model": model,
        "prompt": run["prompt"], "service": run["service"], "profile": run["profile"],
        "usd": rec["usd"], "low": rec["low"], "high": rec["high"], "refused": rec["refused"],
        "truncated": "Y" if args.truncated else "N", "top": rec["top"],
        "raw": answer if len(answer) <= EXCEL_CELL_MAX
               else answer[:EXCEL_CELL_MAX - 60] + "\n[truncated for Excel; full text in data/responses]",
        "notes": rec["notes"] or None, "round": int(run["round"]), "calib": run["calibration"],
    }


def write_row(ws, row_num, rec):
    for key, col in COL.items():
        ws.cell(row_num, col).value = rec[key]


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="Semi-automated ChatGPT run helper.")
    ap.add_argument("--status", action="store_true", help="show progress and exit")
    ap.add_argument("--run", type=int, help="do this run id (must not be logged yet)")
    ap.add_argument("--no-clipboard", action="store_true",
                    help="open files and paste answers by hand instead of using the clipboard")
    ap.add_argument("--truncated", action="store_true",
                    help="mark runs Truncated = Y (only if METHODOLOGY §2.4 forced a cutoff)")
    args = ap.parse_args()

    schedule = load_schedule()
    wb = openpyxl.load_workbook(WORKBOOK)
    ws = wb["Run Log"]
    done, _ = logged(ws)

    todo = [r for r in schedule if int(r["run_id"]) not in done]
    print(f"{len(done)} of {len(schedule)} runs logged.", end=" ")
    if not todo:
        print("All done.")
        return 0
    nxt = todo[0]
    print(f"Next: run {nxt['run_id']} ({nxt['prompt']} {nxt['service']}, "
          f"{'calibration' if nxt['calibration'] == 'Y' else 'round ' + nxt['round']}).")
    gaps = [r["run_id"] for r in todo if int(r["run_id"]) < max(done or [0])]
    if gaps:
        print(f"Skipped earlier runs not yet logged: {', '.join(gaps)}")
    if args.status:
        return 0

    check_writable(WORKBOOK)
    model = ask("\nModel version exactly as ChatGPT shows it", last_model(ws) or "")
    while not model:
        model = ask("Model version (needed for every row)")

    queue = todo
    if args.run:
        queue = [r for r in schedule if int(r["run_id"]) == args.run]
        if not queue:
            sys.exit(f"Run {args.run} is not in the schedule.")
        if args.run in done:
            sys.exit(f"Run {args.run} is already logged (row {done[args.run]}). "
                     "Fix it in Excel instead.")

    for run in queue:
        rec = do_run(run, model, args)
        if rec is None:
            break
        wb = openpyxl.load_workbook(WORKBOOK)       # re-read in case of edits between runs
        ws = wb["Run Log"]
        done, free_row = logged(ws)
        if rec["run_id"] in done:
            print(f"Run {rec['run_id']} was logged meanwhile — not writing it twice.")
            continue
        write_row(ws, free_row, rec)
        save_with_retry(wb, WORKBOOK)
        status = "REFUSED" if rec["refused"] == "Y" else f"${rec['usd']:,}"
        print(f"\n✓ Run {rec['run_id']} logged in row {free_row}: {status}")
        if args.run:
            break
        done_ids = set(done) | {rec["run_id"]}
        left = [r for r in schedule if int(r["run_id"]) not in done_ids]
        if not left:
            print("All runs logged.")
            break
        nxt = left[0]
        if (nxt["prompt"], nxt["round"]) != (run["prompt"], run["round"]):
            print(f"End of {run['prompt']} {'calibration' if run['calibration'] == 'Y' else 'round ' + run['round']}."
                  " Good moment to open the workbook and check the Summary sheet"
                  " (close Excel again before continuing).")
            if nxt["prompt"] != run["prompt"]:
                print(f"That's the whole {run['prompt']} block. Next up is {nxt['prompt']}.")
        if ask(f"Enter = next run ({nxt['run_id']}: {nxt['prompt']} {nxt['service']}), q = stop",
               "").lower() == "q":
            break
    print("Stopped. Run  python log_run.py  again to carry on where you left off.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
