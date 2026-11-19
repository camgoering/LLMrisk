#!/usr/bin/env python3
"""
Build the simple results workbook for the group repo:  handoff/LLM_results.xlsx

    python make_handoff.py

Reads data/llm_run_log.xlsx (calibration runs excluded) and writes four sheets:
About, Summary, Comparison (team column to fill in), All Runs.
"""

import os
import statistics as st

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "data", "llm_run_log.xlsx")
OUT = os.path.join(HERE, "handoff", "LLM_results.xlsx")

SERVICES = ["PayPal", "X", "Google", "ChatGPT", "Netflix", "LinkedIn"]
TOSDR = {"PayPal": "E", "X": "E", "Google": "E", "ChatGPT": "C", "Netflix": "D", "LinkedIn": "C"}
GN = {g: i for i, g in enumerate("ABCDE", 1)}

BOLD = Font(bold=True)
HEAD_FILL = PatternFill("solid", fgColor="DDE4EE")
INPUT_FILL = PatternFill("solid", fgColor="FFF2CC")


def header(ws, cols, widths):
    for i, (c, w) in enumerate(zip(cols, widths), 1):
        cell = ws.cell(1, i, c)
        cell.font, cell.fill = BOLD, HEAD_FILL
        cell.alignment = Alignment(wrap_text=True, vertical="center")
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w
    ws.freeze_panes = "A2"


def main():
    src = openpyxl.load_workbook(SRC, data_only=True)
    rl = src["Run Log"]
    prof = [c.value for c in src["Profiles"][2]]
    runs = []
    for r in range(2, rl.max_row + 1):
        v = [rl.cell(r, c).value for c in range(1, 20)]
        if v[0] is None or v[15] == "Y":       # skip blanks and calibration
            continue
        runs.append(dict(id=v[0], date=v[1], model=v[2], prompt=v[3], service=v[4],
                         usd=v[6], low=v[7], high=v[8], refused=v[9], grade=v[16],
                         tosdr=v[17], notes=v[13], round=v[14], raw=v[12]))

    wb = openpyxl.Workbook()

    # ---------------- About
    ab = wb.active
    ab.title = "About"
    ab.column_dimensions["A"].width = 24
    ab.column_dimensions["B"].width = 100
    dates = sorted({str(x["date"]) for x in runs})
    rows = [
        ("LLM risk estimates", ""),
        ("", ""),
        ("Model", f"ChatGPT web interface, model shown as {runs[0]['model']}, paid (Plus) account"),
        ("Collected", ", ".join(dates)),
        ("Services", ", ".join(SERVICES)),
        ("Design", "6 services × 2 prompts × 5 repeats = 60 scored runs (2 calibration runs excluded). "
                   "New chat every run, first answer only, policy text pasted in, web search off."),
        ("P1 (naive prompt)", "\"What's the risk of accepting this privacy policy in terms of a specific yearly "
                              "dollar amount? Also give it a risk grade from A (lowest risk) to E (highest risk).\" "
                              "+ policy text"),
        ("P2 (profiled prompt)", "Gives a user profile and asks for the expected 12-month cost from identity theft "
                                 "or fraud, with low/high range, A–E grade, top data types and sources, in a fixed "
                                 "format. Full text in the report appendix."),
        ("P2 profile", f"Income ${prof[1]:,}, credit tier {prof[2]}, available credit ${prof[3]:,}, "
                       f"savings ${prof[4]:,} (group means of our survey; no individual's answers were used)"),
        ("ToS;DR", "The prompts never mention ToS;DR. 'Cites ToS;DR' records whether the answer brought it up."),
        ("", ""),
        ("Sheets", ""),
        ("Summary", "Mean, spread and grades per service and prompt"),
        ("Comparison", "Type our team's yearly $ figure per service in the yellow column; ranks and Spearman fill in"),
        ("All Runs", "Every scored run with ChatGPT's full answer"),
        ("", ""),
        ("CV", "Coefficient of variation = SD ÷ mean. Above 0.5 = the dollar figure is not reproducible."),
    ]
    for i, (a, b) in enumerate(rows, 1):
        ab.cell(i, 1, a).font = BOLD
        c = ab.cell(i, 2, b)
        c.alignment = Alignment(wrap_text=True, vertical="top")
    ab["A1"].font = Font(bold=True, size=14)

    # ---------------- Summary
    sm = wb.create_sheet("Summary")
    header(sm, ["Service", "Prompt", "Runs", "Refused", "Mean $/yr", "Median $/yr", "SD", "CV",
                "Min", "Max", "Grades given", "Mean grade (A=1…E=5)", "ToS;DR grade", "Cited ToS;DR"],
           [11, 8, 6, 8, 11, 11, 8, 7, 7, 7, 13, 12, 10, 10])
    r = 2
    for svc in SERVICES:
        for p in ("P1", "P2"):
            sel = [x for x in runs if x["service"] == svc and x["prompt"] == p]
            vals = [float(x["usd"]) for x in sel if x["refused"] != "Y" and isinstance(x["usd"], (int, float))]
            grades = "".join(x["grade"] or "-" for x in sel)
            gnums = [GN[g] for g in grades if g in GN]
            mean = st.mean(vals) if vals else None
            sd = st.stdev(vals) if len(vals) > 1 else None
            row = [svc, p, len(sel), sum(x["refused"] == "Y" for x in sel),
                   round(mean, 1) if mean is not None else None,
                   st.median(vals) if vals else None,
                   round(sd, 1) if sd is not None else None,
                   round(sd / mean, 2) if (sd is not None and mean) else None,
                   min(vals) if vals else None, max(vals) if vals else None,
                   grades, round(st.mean(gnums), 1) if gnums else None, TOSDR[svc],
                   f"{sum(x['tosdr'] == 'Y' for x in sel)}/{len(sel)}"]
            for c, val in enumerate(row, 1):
                sm.cell(r, c, val)
            r += 1

    # ---------------- Comparison
    cp = wb.create_sheet("Comparison")
    header(cp, ["Service", "LLM P1 mean $/yr", "LLM P2 mean $/yr", "Team calc $/yr (type here)",
                "LLM P2 rank", "Team rank", "ToS;DR grade", "LLM P2 mean grade", "LLM P1 mean grade"],
           [11, 12, 12, 16, 10, 10, 10, 12, 12])
    srow = {(sm.cell(i, 1).value, sm.cell(i, 2).value): i for i in range(2, r)}
    for i, svc in enumerate(SERVICES, 2):
        cp.cell(i, 1, svc)
        cp.cell(i, 2, f"=Summary!E{srow[(svc, 'P1')]}")
        cp.cell(i, 3, f"=Summary!E{srow[(svc, 'P2')]}")
        cp.cell(i, 4).fill = INPUT_FILL
        both = f"AND(ISNUMBER($C{i}),ISNUMBER($D{i}))"
        cp.cell(i, 5, f'=IF({both},COUNTIFS($C$2:$C$7,">"&$C{i},$D$2:$D$7,">=0")'
                      f'+(COUNTIFS($C$2:$C$7,$C{i},$D$2:$D$7,">=0")+1)/2,"")')
        cp.cell(i, 6, f'=IF({both},COUNTIFS($D$2:$D$7,">"&$D{i},$C$2:$C$7,">=0")'
                      f'+(COUNTIFS($D$2:$D$7,$D{i},$C$2:$C$7,">=0")+1)/2,"")')
        cp.cell(i, 7, TOSDR[svc])
        cp.cell(i, 8, f"=Summary!L{srow[(svc, 'P2')]}")
        cp.cell(i, 9, f"=Summary!L{srow[(svc, 'P1')]}")
    cp["A9"], cp["A10"] = "Spearman ρ, LLM P2 vs team $", "Services with both"
    cp["B9"] = '=IF(COUNT($E$2:$E$7)<3,"enter team figures",CORREL($E$2:$E$7,$F$2:$F$7))'
    cp["B10"] = "=COUNT($E$2:$E$7)"
    cp["A9"].font = cp["A10"].font = BOLD
    cp["A12"] = ("Ranks: 1 = highest risk, ties averaged, among services that have both figures. "
                 "With 6 services, ρ ≥ 0.89 is needed for p < .05.")

    # ---------------- All Runs
    ar = wb.create_sheet("All Runs")
    header(ar, ["Run", "Date", "Prompt", "Service", "Round", "Annual $", "Low $", "High $", "Refused",
                "Grade", "Cites ToS;DR", "Notes", "ChatGPT's answer"],
           [6, 11, 7, 10, 7, 9, 8, 8, 8, 7, 10, 40, 90])
    for i, x in enumerate(runs, 2):
        raw = (x["raw"] or "").replace("Pasted text", "").strip()
        for c, val in enumerate([x["id"], x["date"], x["prompt"], x["service"], x["round"], x["usd"],
                                 x["low"], x["high"], x["refused"], x["grade"], x["tosdr"],
                                 x["notes"], raw], 1):
            ar.cell(i, c, val)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    wb.save(OUT)
    print(f"wrote {OUT}  ({len(runs)} scored runs)")


if __name__ == "__main__":
    main()
