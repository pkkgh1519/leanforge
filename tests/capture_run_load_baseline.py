import argparse
from pathlib import Path

if __package__:
    from tests.run_load_contract_support import write_captured_baseline
else:
    from run_load_contract_support import write_captured_baseline


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture the exact historical Run load baseline.")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output if args.output.is_absolute() else root / args.output
    write_captured_baseline(root, output.resolve())


if __name__ == "__main__":
    main()
