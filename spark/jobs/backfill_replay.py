"""Validated manual replay entry point."""

import argparse
import json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--symbols-json", required=True)
    args = parser.parse_args()
    symbols = json.loads(args.symbols_json)
    if args.start_date > args.end_date or not symbols:
        raise ValueError("invalid replay scope")
    raise NotImplementedError("Implement bounded partition loop after Bronze contract integration")


if __name__ == "__main__":
    main()
