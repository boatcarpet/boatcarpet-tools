#!/usr/bin/env python3
"""
BoatCarpet manufacturer-year verification companion  (Option A)
================================================================

PURPOSE
  model_years.json is the source of truth for the builder's year dropdowns.
  Most entries hold only `cmc_years` (CMC's range, often a single year or
  a vague guess) and are NOT manufacturer-verified. This tool makes the
  year-verification step *unforgettable and structured*:

    1. It builds a research WORKSHEET for the models you ask about — listing
       the current cmc_years, the flag, and EMPTY slots for verified years
       + source, ready for a human to fill from manufacturer research.
    2. A human (you, or Claude doing the web research WITH you and showing
       sources) fills the worksheet.
    3. It validates the filled worksheet and writes `verified_years`,
       `verification_source`, `verified=true`, `flag="verified"` back into
       model_years.json.

  GATE BEHAVIOR (2026-05-16 — relaxed per locked decision)
  Default: NO confirmation ceremony. A row is written if it has a
  parseable, sane year range AND a non-empty verification_source.
  Manufacturer-sourced years go straight in. Rows with empty years are
  quietly skipped (just not researched yet). `--strict` restores the old
  behavior (also require confirmed=true per row).

  ALWAYS-ON SAFETY (not ceremony — do not remove):
    - year sanity check (rejects pre-1960, future, >40yr spans)
    - verification_source REQUIRED (every written year is traceable)
    - model_years.json backed up before any write

  IMPORTANT — HONEST SCOPE / KNOWN ROUGH EDGES
  This tool does NOT decide years on its own. There is no reliable
  automated source for boat production years; web data conflicts (model
  names get reused across unrelated hull generations). The tool removes
  the "did we remember to check?" risk and gives a structured,
  source-recorded workflow. It does NOT remove human judgement about
  WHICH generation a CMC pattern represents. This tool is a working
  starting point, expected to be refined through use — not a finished,
  fully-validated system. Tested on a couple of models, not all 105.

USAGE
  # 1. Make a worksheet (all unverified patterned models, or filter by make)
  python3 verify_years.py worksheet --make "Four Winns" --out fw_years.json

  # 2. Fill fw_years.json: verified_years + verification_source per row.
  #    (confirmed=true is OPTIONAL now — only matters under --strict.)

  # 3. Apply researched rows into model_years.json (writes a .bak first)
  python3 verify_years.py apply fw_years.json --model-years model_years.json

  # status: how many models still need verification
  python3 verify_years.py status --model-years model_years.json
"""
from __future__ import annotations
import argparse
import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path


YEAR_RE = re.compile(r"^\s*(\d{4})\s*[-–]\s*(\d{4})\s*$")
SINGLE_YEAR_RE = re.compile(r"^\s*(\d{4})\s*$")
THIS_YEAR = date.today().year


def load_my(path: Path) -> dict:
    return json.loads(path.read_text())


def parse_year_range(s: str) -> tuple[int, int] | None:
    """Accept '2003-2007' or '2003' (single). Return (start,end) or None."""
    if not s or not s.strip():
        return None
    m = YEAR_RE.match(s)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return (a, b) if a <= b else (b, a)
    m = SINGLE_YEAR_RE.match(s)
    if m:
        y = int(m.group(1))
        return (y, y)
    return None


def sane_year_range(rng: tuple[int, int]) -> tuple[bool, str]:
    a, b = rng
    if a < 1960:
        return False, f"start year {a} is implausibly early (<1960)"
    if b > THIS_YEAR + 1:
        return False, f"end year {b} is in the future (> {THIS_YEAR+1})"
    if b - a > 40:
        return False, f"range spans {b-a} years — implausibly wide, recheck"
    return True, ""


def cmd_worksheet(args):
    my = load_my(Path(args.model_years))
    models = my["models"]
    rows = []
    for key, v in models.items():
        if not v.get("has_pattern"):
            continue
        if v.get("verified"):
            continue
        if args.make and v.get("make", "").lower() != args.make.lower():
            continue
        cmc = v.get("cmc_years")
        cmc_str = f"{cmc[0]}-{cmc[1]}" if cmc else ""
        rows.append({
            "key": key,
            "make": v.get("make", ""),
            "model": v.get("model", ""),
            "cmc_years": cmc_str,
            "current_flag": v.get("flag", ""),
            # ---- human fills these ----
            "verified_years": "",          # e.g. "1994-2007"
            "verification_source": "",     # URL or citation of where checked
            "generations": [],             # optional: [{"label","years"}]
            "production_gaps": [],         # optional: [[2001,2002]] if any
            "notes": "",
            "confirmed": False,            # set true ONLY when a human is sure
        })
    out = {
        "_worksheet_meta": {
            "purpose": "Fill verified_years + verification_source for each "
                       "row, then set confirmed=true. Run `apply` to write "
                       "back. Unconfirmed rows are ignored, never guessed.",
            "generated": str(date.today()),
            "filter_make": args.make or "(all makes)",
            "row_count": len(rows),
            "instructions": [
                "verified_years: 'YYYY-YYYY' (or single 'YYYY').",
                "verification_source: where you confirmed it (manufacturer "
                "brochure URL, NADA, etc). Required when confirmed=true.",
                "confirmed: true only when a human has checked the source.",
            ],
        },
        "rows": rows,
    }
    Path(args.out).write_text(json.dumps(out, indent=2))
    print(f"Worksheet written: {args.out}")
    print(f"  rows: {len(rows)}  (filter: {args.make or 'all makes'})")
    if rows:
        print("  next: fill verified_years + verification_source, set "
              "confirmed=true, then `apply`.")


def cmd_apply(args):
    ws = json.loads(Path(args.worksheet).read_text())
    my_path = Path(args.model_years)
    my = load_my(my_path)
    models = my["models"]

    # GATE BEHAVIOR (2026-05-16 decision):
    #   Default: NO confirmation ceremony. A row is applied if it has a
    #     parseable, sane year range AND a non-empty verification_source.
    #     Manufacturer-sourced years go straight in (per locked decision:
    #     "when mfg years are looked up, they go in directly").
    #   --strict: restores the original behavior (row must also have
    #     confirmed=true). Kept for anyone who wants the old gate back.
    #
    #   The source requirement and the year-sanity check are NOT ceremony
    #   and remain ALWAYS ON — they are what prevents garbage/typo years
    #   from silently entering the source of truth. Relaxing those would
    #   make the tool unsafe, not convenient.
    strict = getattr(args, "strict", False)

    written, skipped, errors = [], [], []
    for row in ws.get("rows", []):
        key = row.get("key")
        if key not in models:
            errors.append(f"{key}: not found in model_years.json")
            continue
        if strict and not row.get("confirmed"):
            skipped.append(f"{key}: --strict set and confirmed!=true — "
                           f"skipped")
            continue
        raw_years = row.get("verified_years", "")
        if not raw_years or not str(raw_years).strip():
            # Empty year = not yet researched. Quietly skip (not an error;
            # it just means this row hasn't been filled in yet).
            skipped.append(f"{key}: verified_years empty — not yet "
                           f"researched, skipped")
            continue
        rng = parse_year_range(raw_years)
        if not rng:
            errors.append(f"{key}: verified_years "
                          f"'{raw_years}' unparseable (use YYYY-YYYY)")
            continue
        ok, why = sane_year_range(rng)
        if not ok:
            errors.append(f"{key}: {why}")
            continue
        src = (row.get("verification_source") or "").strip()
        if not src:
            errors.append(f"{key}: has years but NO verification_source "
                          f"(source is required — where did the years "
                          f"come from?)")
            continue
        # write back
        m = models[key]
        m["verified_years"] = list(rng)
        m["verification_source"] = src
        m["verified"] = True
        m["flag"] = "verified"
        if row.get("generations"):
            m["generations"] = row["generations"]
        if row.get("production_gaps"):
            m["production_gaps"] = row["production_gaps"]
        if row.get("notes"):
            m["notes"] = row["notes"]
        written.append(f"{key} -> {rng[0]}-{rng[1]}  (src: {src[:50]})")

    if errors and not args.force:
        print("REFUSING TO WRITE — fix these first (or use --force to write "
              "only the clean rows):")
        for e in errors:
            print("  ERROR ", e)
        sys.exit(1)

    if written:
        bak = my_path.with_suffix(".json.bak")
        shutil.copy2(my_path, bak)
        my["_meta"]["last_updated"] = str(date.today())
        my_path.write_text(json.dumps(my, indent=2))
        print(f"Backup: {bak}")
        print(f"Wrote {len(written)} verified rows into {my_path}:")
        for w in written:
            print("  OK    ", w)
    else:
        print("Nothing written (no rows with valid years + source).")

    for s in skipped:
        print("  skip  ", s)
    if errors and args.force:
        print(f"({len(errors)} error rows were skipped due to --force)")
        for e in errors:
            print("  ERROR ", e)


def cmd_status(args):
    my = load_my(Path(args.model_years))
    models = my["models"]
    total = len(models)
    patterned = [v for v in models.values() if v.get("has_pattern")]
    verified = [v for v in patterned if v.get("verified")]
    by_make = {}
    for v in patterned:
        if v.get("verified"):
            continue
        by_make.setdefault(v.get("make", "?"), 0)
        by_make[v.get("make", "?")] += 1
    print(f"model_years.json — {total} models total")
    print(f"  with a pattern:        {len(patterned)}")
    print(f"  year-verified:         {len(verified)}")
    print(f"  patterned, UNverified: {len(patterned) - len(verified)}")
    print()
    print("Unverified patterned models by make:")
    for mk in sorted(by_make):
        print(f"  {mk:24s} {by_make[mk]:3d}")


def main():
    ap = argparse.ArgumentParser(description="Manufacturer year verification "
                                             "companion (Option A)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    w = sub.add_parser("worksheet", help="generate a research worksheet")
    w.add_argument("--model-years", default="model_years.json")
    w.add_argument("--make", default="", help="filter to one make")
    w.add_argument("--out", required=True)
    w.set_defaults(func=cmd_worksheet)

    a = sub.add_parser("apply", help="write researched rows back "
                       "(needs valid years + source; no confirm ceremony)")
    a.add_argument("worksheet")
    a.add_argument("--model-years", default="model_years.json")
    a.add_argument("--force", action="store_true",
                   help="write clean rows even if some rows have errors")
    a.add_argument("--strict", action="store_true",
                   help="restore old behavior: also require confirmed=true "
                        "per row before writing it")
    a.set_defaults(func=cmd_apply)

    s = sub.add_parser("status", help="how many still need verification")
    s.add_argument("--model-years", default="model_years.json")
    s.set_defaults(func=cmd_status)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
