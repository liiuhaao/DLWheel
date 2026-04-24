import os
import zipfile
from pathlib import Path


EXP_LOG_DIR = Path("log")


def _is_safe_target(target: Path, dest: Path) -> bool:
    """Ensure target is within dest and no parent is a symlink."""
    try:
        target.resolve().relative_to(dest.resolve())
    except ValueError:
        return False

    for parent in target.parents:
        if parent == dest or parent == dest.parent:
            break
        if parent.is_symlink():
            return False
    return True


def restore_cli(args):
    src = EXP_LOG_DIR / args.exp_name / "backup.zip"

    if not src.exists():
        print(f"Experiment '{args.exp_name}' not found: {src}")
        return

    dest = Path(args.to).resolve()
    dest.mkdir(parents=True, exist_ok=True)

    conflicts = []
    with zipfile.ZipFile(src, "r") as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            # Skip internal config snapshot
            if info.filename == ".dlwheel-config.yaml":
                continue
            target = dest / info.filename
            if not _is_safe_target(target, dest):
                print(f"Skipping unsafe path: {info.filename}")
                continue
            if target.exists() or target.is_symlink():
                conflicts.append(info.filename)

    if conflicts and not args.force:
        print("The following files will be overwritten:")
        for c in conflicts:
            print(f"  - {c}")
        ans = input("Confirm overwrite? [y/N]: ")
        if ans.lower() not in ("y", "yes"):
            print("Cancelled")
            return

    extracted = []
    with zipfile.ZipFile(src, "r") as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            # Skip internal config snapshot
            if info.filename == ".dlwheel-config.yaml":
                continue
            target = dest / info.filename
            if not _is_safe_target(target, dest):
                continue

            # Remove symlinks before writing to avoid following them
            if target.is_symlink():
                target.unlink()
            target.parent.mkdir(parents=True, exist_ok=True)

            with zf.open(info) as src_f, open(target, "wb") as dst_f:
                dst_f.write(src_f.read())
            extracted.append(info.filename)

    print(f"Restored '{args.exp_name}' to {dest}")
    print(f"Total: {len(extracted)} files")


def add_subparser(subparsers):
    parser = subparsers.add_parser("restore", help="Restore experiment code")
    parser.add_argument("exp_name", help="Experiment name (directory under log/)")
    parser.add_argument("--to", default=".", help="Destination directory (default: current directory)")
    parser.add_argument("--force", action="store_true", help="Overwrite without prompting")
    parser.set_defaults(func=restore_cli)
