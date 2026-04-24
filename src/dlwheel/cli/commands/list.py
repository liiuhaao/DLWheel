import argparse
import zipfile
from datetime import datetime
from pathlib import Path

from dlwheel.utils import format_size


EXP_LOG_DIR = Path("log")


def list_cli(args):
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
        stat = backup_zip.stat()
        with zipfile.ZipFile(backup_zip, "r") as zf:
            file_count = sum(1 for info in zf.infolist() if not info.is_dir())
        experiments.append(
            {
                "name": exp_dir.name,
                "size": stat.st_size,
                "files": file_count,
                "mtime": stat.st_mtime,
            }
        )

    if not experiments:
        print("No experiments found.")
        return

    experiments.sort(key=lambda x: x["mtime"], reverse=True)

    print(f"{'Name':<20} {'Size':>10} {'Files':>8} {'Created':>20}")
    print("-" * 62)
    for exp in experiments:
        created = datetime.fromtimestamp(exp["mtime"]).strftime("%Y-%m-%d %H:%M:%S")
        print(
            f"{exp['name']:<20} {format_size(exp['size']):>10} {exp['files']:>8} {created:>20}"
        )


def add_subparser(subparsers):
    parser = subparsers.add_parser("list", help="List all backed-up experiments")
    parser.set_defaults(func=list_cli)
