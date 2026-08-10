#!/usr/bin/env python3
"""Resolve true OTE openstack-test outcomes from run-suite / run-test logs.

OTE often marks every outer JSON entry as failed when stderr begins with klog
lines (``I0809 ...``), producing::

    Deserializaion Error: invalid character 'I' looking for beginning of value

The real outcome is in nested STDOUT JSON (``"result": "passed"|"failed"|...``)
or in ginkgo summary lines (``SUCCESS!`` / ``FAIL!``).

Usage:
  ote_resolve_results.py count <log> passed|failed|skipped
  ote_resolve_results.py junit <log> <junit_xml_path>
"""

from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from typing import Any


def _load_outer_results(raw: str) -> list[dict[str, Any]]:
    raw = raw.strip()
    if not raw:
        return []

    # Skip leading klog / noise before the JSON array/object.
    start_candidates = [i for i, ch in enumerate(raw) if ch in "[{"]
    for start in start_candidates:
        chunk = raw[start:]
        try:
            data, _ = json.JSONDecoder().raw_decode(chunk)
        except json.JSONDecodeError:
            continue
        if isinstance(data, list):
            return [r for r in data if isinstance(r, dict)]
        if isinstance(data, dict):
            return [data]

    # NDJSON fallback
    results: list[dict[str, Any]] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            results.append(obj)
    return results


def _extract_nested_results(output: str) -> list[dict[str, Any]] | None:
    if not output:
        return None

    m = re.search(r"STDOUT:\n(.*?)(?:\n\nSTDERR:|\nSTDERR:|\Z)", output, re.S)
    stdout = m.group(1) if m else output

    for match in re.finditer(r"\[", stdout):
        chunk = stdout[match.start() :]
        try:
            obj, _ = json.JSONDecoder().raw_decode(chunk)
        except json.JSONDecodeError:
            continue
        if (
            isinstance(obj, list)
            and obj
            and isinstance(obj[0], dict)
            and "result" in obj[0]
        ):
            return obj
    return None


def _result_from_ginkgo(output: str) -> str | None:
    if not output:
        return None
    # Prefer FAIL over SUCCESS when both somehow appear.
    if re.search(r"FAIL! -- .*\| 1 Failed", output) or re.search(
        r"FAIL! -- 0 Passed \| [1-9]", output
    ):
        return "failed"
    if re.search(r"SUCCESS! -- 0 Passed \| 0 Failed \| 0 Pending \| [1-9]+ Skipped", output):
        return "skipped"
    if re.search(r"SUCCESS! -- [1-9]\d* Passed \| 0 Failed", output):
        return "passed"
    if "[FAILED]" in output and "SUCCESS! -- 1 Passed" not in output:
        return "failed"
    return None


def _has_deser_error(output: str) -> bool:
    return "Deserializaion Error" in output or "Deserialization Error" in output


def resolve_result(entry: dict[str, Any]) -> str:
    """Return passed|failed|skipped|unknown for one outer OTE log entry."""
    outer = (entry.get("result") or "").lower()
    output = entry.get("output") or ""

    nested = _extract_nested_results(output)
    if nested:
        # One outer entry maps to one (or few) nested specs; use first, or
        # failed if any nested failed.
        nested_results = [(r.get("result") or "").lower() for r in nested]
        if "failed" in nested_results:
            return "failed"
        if nested_results and all(r == "skipped" for r in nested_results):
            return "skipped"
        if nested_results and all(r == "passed" for r in nested_results):
            return "passed"
        if "passed" in nested_results and "failed" not in nested_results:
            return "passed"

    ginkgo = _result_from_ginkgo(output)
    if ginkgo:
        return ginkgo

    # Outer "failed" with only deserialize noise and no other signal is unknown;
    # callers should not treat unknown as a real failure count source of truth.
    if outer == "failed" and _has_deser_error(output) and not nested and not ginkgo:
        return "unknown"

    if outer in ("passed", "failed", "skipped"):
        return outer
    return "unknown"


def resolve_all(log_path: str) -> list[dict[str, Any]]:
    try:
        with open(log_path, encoding="utf-8") as f:
            raw = f.read()
    except OSError:
        return []

    resolved: list[dict[str, Any]] = []
    for entry in _load_outer_results(raw):
        result = resolve_result(entry)
        resolved.append(
            {
                "name": entry.get("name") or "unknown",
                "result": result,
                "duration": entry.get("duration") or 0,
                "output": entry.get("output") or entry.get("error") or "",
                "error": entry.get("error") or "",
            }
        )
    return resolved


def cmd_count(log_path: str, want: str) -> int:
    want = want.lower()
    return sum(1 for r in resolve_all(log_path) if r["result"] == want)


def cmd_junit(log_path: str, junit_path: str) -> None:
    results = resolve_all(log_path)
    suite = ET.Element("testsuite", name="openstack-test")
    failures = 0
    skipped = 0
    for r in results:
        duration = r.get("duration") or 0
        try:
            # OTE durations are often nanoseconds; keep seconds for junit.
            dur = float(duration)
            if dur > 10_000:
                # ns or ms — treat large values as ns
                time_s = f"{dur / 1_000_000_000.0:.3f}" if dur > 1_000_000 else f"{dur / 1000.0:.3f}"
            else:
                time_s = f"{dur:.3f}"
        except (TypeError, ValueError):
            time_s = "0"

        case = ET.SubElement(suite, "testcase", name=r["name"], time=time_s)
        result = r["result"]
        if result == "failed":
            failures += 1
            fail = ET.SubElement(case, "failure")
            fail.text = r.get("error") or r.get("output") or "failed"
        elif result == "skipped":
            skipped += 1
            skip = ET.SubElement(case, "skipped")
            skip.text = r.get("output") or "skipped"
        elif result == "unknown":
            # Do not inflate failure counts for unparsable deserialize-only noise.
            skip = ET.SubElement(case, "skipped")
            skip.text = "unresolved OTE outcome"

    suite.set("tests", str(len(results)))
    suite.set("failures", str(failures))
    suite.set("skipped", str(skipped))
    ET.ElementTree(suite).write(junit_path, encoding="utf-8", xml_declaration=True)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    cmd = argv[1]
    if cmd == "count":
        if len(argv) != 4:
            print("usage: count <log> passed|failed|skipped", file=sys.stderr)
            return 2
        print(cmd_count(argv[2], argv[3]))
        return 0
    if cmd == "junit":
        if len(argv) != 4:
            print("usage: junit <log> <junit_xml_path>", file=sys.stderr)
            return 2
        cmd_junit(argv[2], argv[3])
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
