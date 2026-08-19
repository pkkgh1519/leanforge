import json
from pathlib import Path

if __package__:
    from tests.run_load_contract_support import verify_baseline
else:
    from run_load_contract_support import verify_baseline


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    result = verify_baseline(root)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
