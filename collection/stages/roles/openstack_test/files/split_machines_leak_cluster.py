#!/usr/bin/env python3
"""Split machines leak-cluster tests out of an OTE test list for serial coda.

Reads the filtered list_of_tests_to_run.txt, writes:
  - leak_cluster_serial.txt: ordered matches for Option B serial run
  - list_of_tests_to_run.txt: remaining tests for the batch suite

Matchers are plain substrings. The MachineSet replica matcher skips any line
that also contains "ControlPlane".
"""
from __future__ import annotations

import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("tests_to_run_path")
    parser.add_argument("leak_cluster_path")
    parser.add_argument(
        "matchers",
        nargs="+",
        help="Ordered substrings to pull into the serial leak-cluster list",
    )
    args = parser.parse_args()

    with open(args.tests_to_run_path, "r", encoding="utf-8") as f:
        lines = [ln.rstrip("\n") for ln in f]

    remaining = list(lines)
    selected: list[str] = []

    for matcher in args.matchers:
        found = None
        for ln in remaining:
            if not ln.strip():
                continue
            if matcher not in ln:
                continue
            if matcher.startswith("MachineSet replica") and "ControlPlane" in ln:
                continue
            if "MachineSet replica number corresponds to the number of Machines" in matcher:
                if "ControlPlane" in ln:
                    continue
            found = ln
            break
        if found is None:
            continue
        selected.append(found)
        remaining = [ln for ln in remaining if ln != found]

    with open(args.leak_cluster_path, "w", encoding="utf-8") as f:
        for ln in selected:
            f.write(ln + "\n")

    with open(args.tests_to_run_path, "w", encoding="utf-8") as f:
        for ln in remaining:
            f.write(ln + "\n")

    print(
        f"leak_cluster={len(selected)} batch_remaining={len([x for x in remaining if x.strip()])}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
