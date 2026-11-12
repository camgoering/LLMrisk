#!/usr/bin/env python3
"""
Summarise the run log for the report.

    python3 analyze.py [path/to/llm_run_log.xlsx]

Reads the Run Log sheet directly (not the Summary sheet's cached values, so it
works whether or not Excel has recalculated) and writes:

    data/summary.csv       n, mean, SD, CV, min, max, refusal rate per service x prompt
    data/ranking.csv       services ranked by LLM mean under P2, ready to pair with
                           the team's ranking for a Spearman correlation

Also prints a Spearman rho between the P1 and P2 rankings, which answers "does
prompt phrasing change the ordering, or only the magnitude?"

Requires: openpyxl
"""

import csv
import os
import statistics as st
import sys
from collections import defaultdict

try:
    import openpyxl
except ImportError:
    sys.exit("Need openpyxl:  pip install openpyxl")

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT = os.path.join(HERE, "data", "llm_run_log.xlsx")


def spearman(a, b):
    """Rank correlation between two equal-length numeric lists."""
    n = len(a)
    if n < 3:
        return None

    def ranks(xs):
        order = sorted(range(n), key=lambda i: xs[i])
        r = [0.0] * n
        i = 0
        while i < n:                      # average ties
            j = i
            while j + 1 < n and xs[order[j + 1]] == xs[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r

    ra, rb = ranks(a), ranks(b)
    ma, mb = sum(ra) / n, sum(rb) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = (sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb)) ** 0.5
    return num / den if den else None


def main(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb["Run Log"]

    vals = defaultdict(list)     # (service, prompt) -> [usd, ...]
    attempts = defaultdict(int)
    refusals = defaultdict(int)

    for row in ws.iter_rows(min_row=2, values_only=True):
        svc, prompt, usd, refused = row[4], row[3], row[6], row[9]
        if not svc or not prompt:
            continue
        key = (svc, prompt)
        attempts[key] += 1
        if str(refused).strip().upper() == "Y":
            refusals[key] += 1
            continue
        if isinstance(usd, (int, float)):
            vals[key].append(float(usd))

    if not attempts:
        print("No runs logged yet — fill in the Run Log sheet first.")
        return 0

    out = os.path.join(os.path.dirname(path), "summary.csv")
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["service", "prompt", "n_scored", "mean_usd", "sd_usd", "cv",
                    "min_usd", "max_usd", "attempts", "refusals", "refusal_rate"])
        print(f"{'service':<12}{'p':<4}{'n':>3}{'mean':>10}{'sd':>10}{'cv':>7}{'refus':>7}")
        print("-" * 53)
        for (svc, prompt) in sorted(attempts):
            v = vals[(svc, prompt)]
            n = len(v)
            mean = st.mean(v) if n else None
            sd = st.stdev(v) if n > 1 else None
            cv = (sd / mean) if (sd and mean) else None
            a, rf = attempts[(svc, prompt)], refusals[(svc, prompt)]
            w.writerow([svc, prompt, n,
                        f"{mean:.0f}" if mean else "", f"{sd:.0f}" if sd else "",
                        f"{cv:.3f}" if cv else "",
                        f"{min(v):.0f}" if v else "", f"{max(v):.0f}" if v else "",
                        a, rf, f"{rf/a:.3f}"])
            print(f"{svc:<12}{prompt:<4}{n:>3}"
                  f"{(f'{mean:,.0f}' if mean else '-'):>10}"
                  f"{(f'{sd:,.0f}' if sd else '-'):>10}"
                  f"{(f'{cv:.2f}' if cv else '-'):>7}"
                  f"{f'{rf}/{a}':>7}")

    # ranking under P2, for pairing with the team's ranking
    p2 = {s: st.mean(v) for (s, p), v in vals.items() if p == "P2" and v}
    rank_path = os.path.join(os.path.dirname(path), "ranking.csv")
    with open(rank_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["service", "llm_mean_usd_P2", "llm_rank", "team_calc_usd", "team_rank"])
        for i, (s, m) in enumerate(sorted(p2.items(), key=lambda kv: -kv[1]), 1):
            w.writerow([s, f"{m:.0f}", i, "", ""])

    p1 = {s: st.mean(v) for (s, p), v in vals.items() if p == "P1" and v}
    both = sorted(set(p1) & set(p2))
    if len(both) >= 3:
        rho = spearman([p1[s] for s in both], [p2[s] for s in both])
        print(f"\nSpearman rho, P1 ranking vs P2 ranking (n={len(both)}): "
              f"{rho:.2f}" if rho is not None else "")
        print("  High rho means prompt phrasing moves the magnitude but not the ordering.")

    print(f"\nwrote {out}\nwrote {rank_path}")
    print("Fill the team_calc_usd column in ranking.csv, then report Spearman rho "
          "between llm_rank and team_rank.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else DEFAULT))
