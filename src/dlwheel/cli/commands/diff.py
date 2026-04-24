import argparse
import zipfile
from pathlib import Path

from pathspec import GitIgnoreSpec


EXP_LOG_DIR = Path("log")
_DIFF_LIMIT = 20

ANSI = {
    "header": "\033[36m",
    "add": "\033[32m",
    "remove": "\033[31m",
    "reset": "\033[0m",
}


def _load_gitignore():
    gitignore_path = Path(".gitignore")
    if not gitignore_path.exists():
        return GitIgnoreSpec([])
    with gitignore_path.open("r") as f:
        return GitIgnoreSpec.from_lines(f)


def _should_ignore(path, spec):
    git_style_path = path.relative_to(Path.cwd()).as_posix()
    if path.is_dir():
        git_style_path += "/"
    return spec.match_file(git_style_path)


def _print_file_list(title, files, color_key):
    if not files:
        return
    print(f"\n{ANSI[color_key]}{title} ({len(files)}):{ANSI['reset']}")
    for f in files[:_DIFF_LIMIT]:
        prefix = "+" if color_key == "add" else "-" if color_key == "remove" else "~"
        print(f"  {prefix} {f}")
    if len(files) > _DIFF_LIMIT:
        print(f"  ... and {len(files) - _DIFF_LIMIT} more")


def diff_cli(args):
    src = EXP_LOG_DIR / args.exp_name / "backup.zip"
    if not src.exists():
        print(f"Experiment '{args.exp_name}' not found: {src}")
        return

    ignore_spec = _load_gitignore()
    backup_files = {}
    backup_contents = {}

    with zipfile.ZipFile(src, "r") as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            if info.filename == ".dlwheel-config.yaml":
                continue
            backup_files[info.filename] = info
            with zf.open(info) as f:
                backup_contents[info.filename] = f.read()

    current_files = set()
    for file_path in Path.cwd().rglob("*"):
        rel = file_path.relative_to(Path.cwd()).as_posix()
        if rel.startswith("log/") or rel == "log":
            continue
        if rel.startswith(".venv/") or rel == ".venv":
            continue
        if rel.startswith(".git/") or rel == ".git":
            continue
        if rel == ".dlwheel-config.yaml":
            continue
        if _should_ignore(file_path, ignore_spec):
            continue
        if not file_path.is_file():
            continue
        current_files.add(rel)

    added = sorted(f for f in current_files if f not in backup_files)
    removed = sorted(f for f in backup_files if f not in current_files)
    modified = []
    for f in sorted(current_files):
        if f not in backup_files:
            continue
        info = backup_files[f]
        if Path(f).stat().st_size != info.file_size:
            modified.append(f)
            continue
        if backup_contents[f] != Path(f).read_bytes():
            modified.append(f)

    if not (added or removed or modified):
        print("No differences found.")
        return

    _print_file_list("Added", added, "add")
    _print_file_list("Removed", removed, "remove")
    _print_file_list("Modified", modified, "header")


def add_subparser(subparsers):
    parser = subparsers.add_parser(
        "diff", help="Compare current directory with a backed-up experiment"
    )
    parser.add_argument("exp_name", help="Experiment name (directory under log/)")
    parser.set_defaults(func=diff_cli)
