#!/usr/bin/env python3
"""Split serial-coda tests out of an OTE test list.

Reads the filtered list_of_tests_to_run.txt and an ordered matchers file
(one substring per line), writes:
  - leak_cluster_serial.txt: ordered matches for serial coda
    (Machine leak cluster, suite-load flakes, topology pair)
  - list_of_tests_to_run.txt: remaining tests for the batch suite

Matchers are plain substrings (one full phrase per line). The MachineSet
replica matcher skips any line that also contains "ControlPlane".

When any matcher hits, every matcher must resolve to exactly one test;
missing or non-unique matches fail hard. Zero hits keep the allowlist
no-op (empty serial file, batch unchanged).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def load_matchers(path: str) -> list[str]:
    with open(path, "r", encoding="utf-8") as f:
        return [ln.strip() for ln in f if ln.strip() and not ln.strip().startswith("#")]


def pick(remaining: list[str], matcher: str) -> list[str]:
    """Return all candidate lines for matcher (ControlPlane skipped for MachineSet replica)."""
    candidates: list[str] = []
    for ln in remaining:
        if not ln.strip():
            continue
        if matcher not in ln:
            continue
        # Avoid ControlPlane MachineSet when matching worker MachineSet replica.
        if "MachineSet replica number corresponds to the number of Machines" in matcher:
            if "ControlPlane" in ln:
                continue
        candidates.append(ln)
    return candidates


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("tests_to_run_path")
    parser.add_argument("leak_cluster_path")
    parser.add_argument("matchers_file")
    args = parser.parse_args()

    matchers = load_matchers(args.matchers_file)
    if not matchers:
        print("leak_cluster=0 batch_remaining=unchanged (empty matchers file)")
        Path(args.leak_cluster_path).write_text("", encoding="utf-8")
        return 0

    with open(args.tests_to_run_path, "r", encoding="utf-8") as f:
        lines = [ln.rstrip("\n") for ln in f]

    remaining = list(lines)
    resolved: list[tuple[str, list[str]]] = []
    any_hit = False

    for matcher in matchers:
        candidates = pick(remaining, matcher)
        if candidates:
            any_hit = True
        resolved.append((matcher, candidates))

    if not any_hit:
        # Allowlist no-op: none of the coda tests are in this filtered list.
        print("leak_cluster=0 batch_remaining=unchanged (no matchers hit)")
        Path(args.leak_cluster_path).write_text("", encoding="utf-8")
        return 0

    selected: list[str] = []
    for matcher, candidates in resolved:
        if len(candidates) == 0:
            print(
                f"error: matcher matched no tests: {matcher!r}",
                file=sys.stderr,
            )
            return 1
        if len(candidates) > 1:
            print(
                f"error: matcher matched {len(candidates)} tests (expected 1): {matcher!r}",
                file=sys.stderr,
            )
            for c in candidates:
                print(f"  candidate: {c}", file=sys.stderr)
            return 1
        selected.append(candidates[0])
        remaining = [ln for ln in remaining if ln != candidates[0]]

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
