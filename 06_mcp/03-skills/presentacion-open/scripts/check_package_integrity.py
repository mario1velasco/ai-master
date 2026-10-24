#!/usr/bin/env python3
"""Check PPTX ZIP integrity and that python-pptx can read the package."""
from __future__ import annotations

import argparse
from collections import Counter
import sys
import zipfile
from pathlib import Path
from typing import List

from pptx import Presentation

REQUIRED_PARTS = {"[Content_Types].xml", "_rels/.rels", "ppt/presentation.xml"}


def inspect(path: Path) -> List[str]:
    issues: List[str] = []
    try:
        with zipfile.ZipFile(path, "r") as package:
            names = package.namelist()
            missing = REQUIRED_PARTS.difference(names)
            if missing:
                issues.append("missing required package part(s): {}".format(", ".join(sorted(missing))))
            duplicate_names = sorted(name for name, count in Counter(names).items() if count > 1)
            if duplicate_names:
                issues.append("duplicate ZIP part name(s): {}".format(", ".join(duplicate_names)))
            corrupt = package.testzip()
            if corrupt:
                issues.append("ZIP CRC check failed for {}".format(corrupt))
    except (OSError, zipfile.BadZipFile) as exc:
        return ["invalid PPTX ZIP package: {}".format(exc)]
    if not issues:
        try:
            presentation = Presentation(str(path))
            if not presentation.slides:
                issues.append("presentation contains no slides")
        except Exception as exc:
            issues.append("python-pptx could not open package: {}".format(exc))
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Check ZIP CRCs, required OPC parts, and python-pptx readability")
    parser.add_argument("presentation", type=Path)
    args = parser.parse_args()
    path = args.presentation.resolve()
    if not path.is_file():
        parser.error("PPTX not found: {}".format(path))
    issues = inspect(path)
    if issues:
        print("Package integrity issues:")
        for issue in issues:
            print("- " + issue)
        return 1
    print("OK: PPTX ZIP package is intact and opens with python-pptx.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
