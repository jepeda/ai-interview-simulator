"""Manage your exercise working copies.

  uv run python scripts/workspace.py init            create any missing working files from the starters
  uv run python scripts/workspace.py reset py03      restore one exercise (several ids allowed)
  uv run python scripts/workspace.py reset --all     restore every exercise
  uv run python scripts/workspace.py status          show which exercises you have modified

npm shortcuts:  npm run reset -- py03   |   npm run reset -- --all   |   npm run status
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from trainer import progress  # noqa: E402
from trainer.catalog import load_catalog  # noqa: E402
from trainer.paths import rel  # noqa: E402
from trainer.workspace import init_workspace, is_modified, reset_files  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    reset = sub.add_parser("reset")
    reset.add_argument("ids", nargs="*", help="exercise ids, e.g. py03 dbg2")
    reset.add_argument("--all", action="store_true")
    reset.add_argument("--keep-progress", action="store_true", help="only restore files")
    sub.add_parser("status")
    args = parser.parse_args()

    catalog = load_catalog()

    if args.command == "init":
        created = init_workspace()
        print(f"Workspace ready ({len(created)} file(s) created).")
        for path in created:
            print(f"  + {rel(path)}")
        return 0

    if args.command == "reset":
        ids = list(catalog) if args.all else args.ids
        if not ids:
            parser.error("give exercise ids (e.g. py03) or --all")
        unknown = [i for i in ids if i not in catalog]
        if unknown:
            print(f"Unknown exercise id(s): {', '.join(unknown)}. Known: {', '.join(catalog)}")
            return 1
        for ex_id in ids:
            for path in reset_files(catalog[ex_id].files):
                print(f"  restored {rel(path)}")
            if not args.keep_progress:
                progress.reset(ex_id)
            print(f"Reset {ex_id}: {catalog[ex_id].title}")
        return 0

    for ex in catalog.values():
        state = "modified" if any(is_modified(f) for f in ex.files) else "pristine"
        print(f"{ex.id:6} {state:9} {ex.title}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
