#!/usr/bin/env python3
"""
Summarise the run log for the report.

    python analyze.py [path/to/llm_run_log.xlsx]

Reads the Run Log sheet directly (not the Summary sheet's cached values, so it
works whether or not Excel has recalculated) and the team's figures from column D
of the Comparison sheet. Rows with Calibration = Y are excluded throughout.

Writes, next to the workbook:

    summary.csv    n, mean, SD, CV, min, max, refusal rate per service x prompt
    refusals.csv   refusal rate per prompt condition, pooled over services
    ranking.csv    LLM mean and rank per service under P1 and P2, beside the
                   team's figure and rank

Prints Spearman's rho, with an exact permutation p-value, for:
    P1 ranking vs P2 ranking   does prompt phrasing change the ordering?
    P1 vs team, P2 vs team     does the LLM order services the way we do?

Requires: openpyxl
"""

import csv
import itertools
import math
import os
import random
import statistics as st
import sys
from collections import defaultdict

try:
    import openpyxl
except ImportError:
    sys.exit("Need openpyxl:  pip install openpyxl")

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT = os.path.join(HERE, "data", "llm_run_log.xlsx")

# Run Log columns (0-based)
C_PROMPT, C_SERVICE, C_USD, C_REFUSED, C_TRUNC, C_ROUND, C_CALIB = 3, 4, 6, 9, 10, 14, 15
C_GRADE, C_TOSDR, C_SOURCES = 16, 17, 18          # prompts v2.0 only
GRADE_NUM = {g: i for i, g in enumerate("ABCDE", 1)}


def is_yes(v):
    return str(v).strip().upper() == "Y"


def ranks(xs, descending=True):
    """1 = largest when descending; ties get the average rank."""
    n = len(xs)
    order = sorted(range(n), key=lambda i: -xs[i] if descending else xs[i])
    r = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def pearson(a, b):
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den = math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))
    return num / den if den else None


def spearman(a, b):
    """(rho, two-sided exact permutation p) for paired lists; (None, None) if n < 3.

    Exact enumeration for n <= 9; for larger n (e.g. run-level correlations) a
    20,000-permutation Monte Carlo estimate with a fixed seed.
    """
    if len(a) < 3:
        return None, None
    ra, rb = ranks(a), ranks(b)
    rho = pearson(ra, rb)
    if rho is None:
        return rho, None
    if len(a) > 9:                          # Monte Carlo permutation test, fixed seed
        rng = random.Random(469)
        perm, hits, total = list(rb), 0, 20000
        for _ in range(total):
            rng.shuffle(perm)
            r = pearson(ra, perm)
            if r is not None and abs(r) >= abs(rho) - 1e-12:
                hits += 1
        return rho, (hits + 1) / (total + 1)
    hits = total = 0
    for perm in itertools.permutations(rb):
        r = pearson(ra, perm)
        total += 1
        if r is not None and abs(r) >= abs(rho) - 1e-12:
            hits += 1
    return rho, hits / total


def fmt(x, spec):
    return "" if x is None else format(x, spec)


def main(path):
    if not os.path.exists(path):
        sys.exit(f"Workbook not found: {path}")
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb["Run Log"]

    vals = defaultdict(list)        # (service, prompt) -> [usd, ...]
    attempts = defaultdict(int)
    refusals = defaultdict(int)
    truncated = defaultdict(int)
    skipped_calib = 0
    grades = defaultdict(list)      # (service, prompt) -> ["D", ...]
    no_grade = defaultdict(int)
    tosdr = defaultdict(int)
    pairs = defaultdict(list)       # prompt -> [(usd, grade_num)] for runs with both
    graded_runs = []                # (service, prompt, grade, cites_tosdr)

    for row in ws.iter_rows(min_row=2, values_only=True):
        row = list(row) + [None] * (19 - len(row))
        svc, prompt = row[C_SERVICE], row[C_PROMPT]
        if not svc or not prompt:
            continue
        if is_yes(row[C_CALIB]):
            skipped_calib += 1
            continue
        key = (svc, prompt)
        attempts[key] += 1
        if is_yes(row[C_TRUNC]):
            truncated[key] += 1
        g = str(row[C_GRADE] or "").strip().upper()[:1]
        if g in GRADE_NUM:
            grades[key].append(g)
            graded_runs.append((svc, prompt, g, is_yes(row[C_TOSDR])))
            if isinstance(row[C_USD], (int, float)) and not is_yes(row[C_REFUSED]):
                pairs[prompt].append((float(row[C_USD]), GRADE_NUM[g]))
        else:
            no_grade[key] += 1
        if is_yes(row[C_TOSDR]):
            tosdr[key] += 1
        if is_yes(row[C_REFUSED]):
            refusals[key] += 1
            continue
        if isinstance(row[C_USD], (int, float)):
            vals[key].append(float(row[C_USD]))

    if not attempts:
        print("No scored runs logged yet — fill in the Run Log sheet first.")
        return 0

    outdir = os.path.dirname(os.path.abspath(path))

    # ---- per service x prompt
    out = os.path.join(outdir, "summary.csv")
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["service", "prompt", "n_scored", "mean_usd", "sd_usd", "cv",
                    "min_usd", "max_usd", "attempts", "refusals", "refusal_rate",
                    "truncated_runs"])
        print(f"{'service':<12}{'p':<4}{'n':>3}{'mean':>11}{'sd':>11}{'cv':>7}{'refused':>9}")
        print("-" * 57)
        for key in sorted(attempts):
            v = vals[key]
            n = len(v)
            mean = st.mean(v) if n else None
            sd = st.stdev(v) if n > 1 else None
            cv = sd / mean if (sd is not None and mean) else None
            a, rf = attempts[key], refusals[key]
            w.writerow([*key, n, fmt(mean, ".0f"), fmt(sd, ".0f"), fmt(cv, ".3f"),
                        fmt(min(v) if v else None, ".0f"), fmt(max(v) if v else None, ".0f"),
                        a, rf, f"{rf / a:.3f}", truncated[key]])
            print(f"{key[0]:<12}{key[1]:<4}{n:>3}{fmt(mean, ',.0f') or '-':>11}"
                  f"{fmt(sd, ',.0f') or '-':>11}{fmt(cv, '.2f') or '-':>7}{f'{rf}/{a}':>9}")

    # ---- refusal rate per prompt condition
    ref_path = os.path.join(outdir, "refusals.csv")
    by_prompt = defaultdict(lambda: [0, 0])
    for (svc, p), a in attempts.items():
        by_prompt[p][0] += refusals[(svc, p)]
        by_prompt[p][1] += a
    with open(ref_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["prompt", "refusals", "attempts", "refusal_rate"])
        print("\nRefusal rate by prompt:")
        for p in sorted(by_prompt):
            rf, a = by_prompt[p]
            w.writerow([p, rf, a, f"{rf / a:.3f}"])
            print(f"  {p}: {rf}/{a} = {rf / a:.0%}")

    # ---- rankings and Spearman
    means = {p: {s: st.mean(v) for (s, pp), v in vals.items() if pp == p and v}
             for p in ("P1", "P2")}
    team = {}
    if "Comparison" in wb.sheetnames:
        for row in wb["Comparison"].iter_rows(min_row=2, max_col=4, values_only=True):
            if row[0] and isinstance(row[3], (int, float)):
                team[row[0]] = float(row[3])

    services = sorted(set(means["P1"]) | set(means["P2"]) | set(team))

    def rank_map(d):
        keys = [s for s in services if s in d]
        return dict(zip(keys, ranks([d[s] for s in keys])))

    r1, r2, rt = rank_map(means["P1"]), rank_map(means["P2"]), rank_map(team)
    rank_path = os.path.join(outdir, "ranking.csv")
    with open(rank_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["service", "llm_mean_usd_P1", "llm_rank_P1", "llm_mean_usd_P2",
                    "llm_rank_P2", "team_calc_usd", "team_rank"])
        for s in sorted(services, key=lambda s: r2.get(s, 99)):
            w.writerow([s, fmt(means["P1"].get(s), ".0f"), fmt(r1.get(s), "g"),
                        fmt(means["P2"].get(s), ".0f"), fmt(r2.get(s), "g"),
                        fmt(team.get(s), ".0f"), fmt(rt.get(s), "g")])

    print("\nSpearman's rho (ranks among services present in both; 1 = highest risk):")
    for label, a, b in [("P1 vs P2  ", means["P1"], means["P2"]),
                        ("P1 vs team", means["P1"], team),
                        ("P2 vs team", means["P2"], team)]:
        both = [s for s in services if s in a and s in b]
        rho, p = spearman([a[s] for s in both], [b[s] for s in both])
        if rho is None:
            why = "no team figures yet" if b is team and not team else "need 3+ services"
            print(f"  {label}  n={len(both)}  -  ({why})")
        else:
            print(f"  {label}  n={len(both)}  rho = {rho:+.2f}"
                  + (f"   exact p = {p:.3f}" if p is not None else ""))
    print("  With n = 6, |rho| must be about 0.89 or more for p < .05 — report rho"
          " as descriptive, not as a significance test, unless it clears that.")

    # ---- grades vs ToS;DR
    ref = {}
    if "Services" in wb.sheetnames:
        for row in wb["Services"].iter_rows(min_row=2, max_col=3, values_only=True):
            if row[0] and str(row[2] or "").strip().upper() in GRADE_NUM:
                ref[row[0]] = str(row[2]).strip().upper()
    grade_path = None
    if grades or any(tosdr.values()):
        grade_path = os.path.join(outdir, "grades.csv")
        with open(grade_path, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["service", "prompt", "n_graded", "A", "B", "C", "D", "E",
                        "mean_grade_1to5", "modal_grade", "tosdr_grade", "exact_match_rate",
                        "within_one_rate", "no_grade", "cites_tosdr", "attempts"])
            print(f"\n{'service':<12}{'p':<4}{'grades':<14}{'mean':>6}{'ToS;DR':>8}{'match':>7}{'cites':>7}")
            print("-" * 58)
            for key in sorted(attempts):
                gl = grades[key]
                nums = [GRADE_NUM[g] for g in gl]
                mean_g = st.mean(nums) if nums else None
                counts = [gl.count(g) for g in "ABCDE"]
                modal = "/".join(g for g, c in zip("ABCDE", counts) if c == max(counts)) if gl else ""
                rg = ref.get(key[0])
                exact = (sum(g == rg for g in gl) / len(gl)) if (gl and rg) else None
                near = (sum(abs(GRADE_NUM[g] - GRADE_NUM[rg]) <= 1 for g in gl) / len(gl)) if (gl and rg) else None
                w.writerow([*key, len(gl), *counts, fmt(mean_g, ".2f"), modal, rg or "",
                            fmt(exact, ".2f"), fmt(near, ".2f"), no_grade[key], tosdr[key], attempts[key]])
                print(f"{key[0]:<12}{key[1]:<4}{''.join(gl) or '-':<14}{fmt(mean_g, '.2f') or '-':>6}"
                      f"{rg or '-':>8}{fmt(exact, '.0%') or '-':>7}{f'{tosdr[key]}/{attempts[key]}':>7}")

        print("\nToS;DR mentioned, by prompt:")
        for p in sorted({k[1] for k in attempts}):
            c = sum(v for k, v in tosdr.items() if k[1] == p)
            a = sum(v for k, v in attempts.items() if k[1] == p)
            print(f"  {p}: {c}/{a} = {c / a:.0%}")

        print("\nSpearman's rho, LLM mean grade vs ToS;DR grade (A=1 … E=5):")
        for p in ("P1", "P2"):
            mg = {s: st.mean(GRADE_NUM[g] for g in gl) for (s, pp), gl in grades.items() if pp == p and gl}
            both = [s for s in sorted(mg) if s in ref]
            rho, pv = spearman([mg[s] for s in both], [GRADE_NUM[ref[s]] for s in both])
            print(f"  {p}  n={len(both)}  " + ("-  (need 3+ services)" if rho is None else
                  f"rho = {rho:+.2f}" + (f"   exact p = {pv:.3f}" if pv is not None else "")))
        print("  ToS;DR's six grades include ties (E, E, E, D, C, C), which caps how high rho can go.")

        print("\nGrade matches ToS;DR exactly — runs that mention ToS;DR vs runs that don't:")
        for label, flag in (("mention ToS;DR", True), ("don't mention", False)):
            sel = [(s_, g) for s_, _, g, c in graded_runs if c == flag and s_ in ref]
            if sel:
                m = sum(g == ref[s_] for s_, g in sel)
                print(f"  {label:<15} {m}/{len(sel)} = {m / len(sel):.0%}")
            else:
                print(f"  {label:<15} -")
        print("  Much higher agreement when ToS;DR is mentioned suggests the grade is recalled,"
              " not judged from the policy.")

        print("\nDoes the grade agree with the dollar figure? (run level, Spearman)")
        for p in sorted(pairs):
            xs, ys = zip(*pairs[p]) if pairs[p] else ((), ())
            rho, pv = spearman(list(xs), list(ys))
            print(f"  {p}  n={len(xs)}  " + ("-" if rho is None else
                  f"rho = {rho:+.2f}" + (f"   p ≈ {pv:.3f}" if pv is not None else "")))

    if skipped_calib:
        print(f"\n{skipped_calib} calibration run(s) excluded.")
    mixed = {k for k in attempts if 0 < truncated[k] < attempts[k]}
    if mixed:
        print("WARNING: truncation is mixed within", ", ".join(f"{s} {p}" for s, p in sorted(mixed)))
    print(f"\nwrote {out}\nwrote {ref_path}\nwrote {rank_path}" + (f"\nwrote {grade_path}" if grade_path else ""))
    if not team:
        print("Type the team's figures into Comparison column D, then run this again.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else DEFAULT))
