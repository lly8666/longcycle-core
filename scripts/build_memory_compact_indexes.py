from __future__ import annotations

import argparse
from pathlib import Path

from longcycle.application.memory_index import write_shard_memory_index


def build_indexes(campaign_dir: Path, output_dir: Path) -> int:
    blind_dir = campaign_dir / "blind"
    if not blind_dir.is_dir():
        raise FileNotFoundError(f"blind campaign directory not found: {blind_dir}")

    shard_dirs = tuple(sorted(path for path in blind_dir.iterdir() if path.is_dir()))
    if not shard_dirs:
        raise ValueError(f"no shard directories found under {blind_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    for shard_dir in shard_dirs:
        write_shard_memory_index(
            shard_dir,
            output_dir / f"{shard_dir.name}.json",
        )
    return len(shard_dirs)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build replaceable deterministic compact indexes from blind Memory Leads."
    )
    parser.add_argument("campaign_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    count = build_indexes(args.campaign_dir, args.output_dir)
    print(f"built {count} shard compact indexes in {args.output_dir}")


if __name__ == "__main__":
    main()
