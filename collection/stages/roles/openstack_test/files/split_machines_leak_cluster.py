#!/usr/bin/env python3
"""Split machines leak-cluster tests out of an OTE test list for serial coda.

Reads the filtered list_of_tests_to_run.txt and an ordered matchers file
(one substring per line), writes:
  - leak_cluster_serial.txt: ordered matches for Option B serial run
  - list_of_tests_to_run.txt: remaining tests for the batch suite

Matchers are plain substrings (one full phrase per line). The MachineSet
replica matcher skips any line that also contains "ControlPlane".
"""
from __future__ import annotations

import argparse
import sys


def load_matchers(path: str) -> list[str]:
    with open(path, "r", encoding="utf-8") as f:
        return [ln.strip() for ln in f if ln.strip() and not ln.strip().startswith("#")]


def pick(remaining: list[str], matcher: str) -> str | None:
    for ln in remaining:
        if not ln.strip():
            continue
        if matcher not in ln:
            continue
        # Avoid ControlPlane MachineSet when matching worker MachineSet replica.
        if "MachineSet replica number corresponds to the number of Machines" in matcher:
            if "ControlPlane" in ln:
                continue
        return ln
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("tests_to_run_path")
    parser.add_argument("leak_cluster_path")
    parser.add_argument(
        "matchers_file",
        help="File with one matcher substring per line (ordered)",
    )
    args = parser.parse_args()

    matchers = load_matchers(args.matchers_file)
    if not matchers:
        print("leak_cluster=0 batch_remaining=unchanged (empty matchers file)")
        open(args.leak_cluster_path, "w", encoding="utf-8").close()
        return 0

    with open(args.tests_to_run_path, "r", encoding="utf-8") as f:
        lines = [ln.rstrip("\n") for ln in f]

    remaining = list(lines)
    selected: list[str] = []

    for matcher in matchers:
        found = pick(remaining, matcher)
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
