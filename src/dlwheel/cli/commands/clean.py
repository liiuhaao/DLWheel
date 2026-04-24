import argparse
import shutil
import time
from pathlib import Path


EXP_LOG_DIR = Path("log")


def clean_cli(args):
    if not EXP_LOG_DIR.exists():
        print("No experiments found.")
        return

    experiments = []
    for exp_dir in EXP_LOG_DIR.iterdir():
        if not exp_dir.is_dir():
            continue
        backup_zip = exp_dir / "backup.zip"
        if not backup_zip.exists():
            continue
        experiments.append((exp_dir, backup_zip.stat().st_mtime))

    if not experiments:
        print("No experiments found.")
        return

    to_delete = []

    if args.keep is not None:
        experiments.sort(key=lambda x: x[1], reverse=True)
        to_delete = experiments[args.keep:]
    elif args.older_than is not None:
        cutoff = time.time() - args.older_than * 86400
        to_delete = [(d, t) for d, t in experiments if t < cutoff]
    else:
        print("Please specify --keep or --older-than.")
        return

    if not to_delete:
        print("Nothing to clean.")
        return

    print(f"Will delete {len(to_delete)} experiment(s):")
    for d, _ in to_delete:
        print(f"  - {d.name}")

    if not args.force:
        ans = input("Confirm? [y/N]: ")
        if ans.lower() not in ("y", "yes"):
            print("Cancelled.")
            return

    for d, _ in to_delete:
        shutil.rmtree(d)
        print(f"Deleted {d.name}")

    print(f"Cleaned {len(to_delete)} experiment(s).")


def add_subparser(subparsers):
    parser = subparsers.add_parser("clean", help="Clean up old experiment backups")
    parser.add_argument("--keep", type=int, help="Keep the N most recent experiments")
    parser.add_argument(
        "--older-than", type=int, metavar="DAYS", help="Delete experiments older than N days"
    )
    parser.add_argument("--force", action="store_true", help="Delete without prompting")
    parser.set_defaults(func=clean_cli)
