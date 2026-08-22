#!/usr/bin/env python3
"""Write one Adaptive Assurance shadow decision without changing Prime or Run flow."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from adaptive_assurance import ContractError, load_json, shadow_payload


def write_atomic(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    os.replace(tmp, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--case", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        contract = load_json(args.contract)
        case = load_json(args.case)
        write_atomic(args.output, shadow_payload(case, contract))
    except ContractError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
