import argparse
import zipfile
from datetime import datetime
from pathlib import Path

from dlwheel.utils import format_size


EXP_LOG_DIR = Path("log")


def show_cli(args):
    src = EXP_LOG_DIR / args.exp_name / "backup.zip"
    if not src.exists():
        print(f"Experiment '{args.exp_name}' not found: {src}")
        return

    stat = src.stat()
    with zipfile.ZipFile(src, "r") as zf:
        file_count = sum(1 for info in zf.infolist() if not info.is_dir())
        config_content = ""
        if ".dlwheel-config.yaml" in zf.namelist():
            config_content = zf.read(".dlwheel-config.yaml").decode("utf-8", errors="replace")

    created = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    print(f"Experiment : {args.exp_name}")
    print(f"Size       : {format_size(stat.st_size)}")
    print(f"Files      : {file_count}")
    print(f"Created    : {created}")
    if config_content:
        print(f"\nConfig snapshot:")
        for line in config_content.splitlines():
            print(f"  {line}")


def add_subparser(subparsers):
    parser = subparsers.add_parser("show", help="Show details of a backed-up experiment")
    parser.add_argument("exp_name", help="Experiment name (directory under log/)")
    parser.set_defaults(func=show_cli)
