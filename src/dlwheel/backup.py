import shutil
import warnings
import zipfile
from pathlib import Path

import yaml
from pathspec import GitIgnoreSpec


# Default threshold: 100MB
_DEFAULT_MAX_SIZE = 100 * 1024 * 1024


class BackupSystem:
    def __init__(self, cfg):
        self.cfg = cfg
        log_path = cfg.path.log if cfg.path and cfg.path.log else f"log"
        self.backup_dir = Path(log_path) / cfg.name
        # Handle cfg.backup being either a bool or a dict
        backup_cfg = cfg.get("backup", {}) if isinstance(cfg.get("backup"), dict) else {}
        self.max_file_size = self._parse_size(
            backup_cfg.get("max_file_size", _DEFAULT_MAX_SIZE)
        )
        # User-defined exclude patterns (e.g. ["data/", "*.pth"])
        exclude_patterns = backup_cfg.get("exclude", [])
        self.exclude_spec = GitIgnoreSpec.from_lines(exclude_patterns) if exclude_patterns else GitIgnoreSpec([])

    def run(self):
        if self.backup_dir.exists() and self.cfg.resume:
            return

        shutil.rmtree(self.backup_dir, ignore_errors=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self._create_backup_zip()

    def _parse_size(self, value):
        """Parse a size string such as '100MB', '1GB', '512KB', or a plain number (bytes)."""
        if isinstance(value, (int, float)):
            return int(value)

        s = str(value).strip().upper()
        # Match longer units first to avoid "MB" being matched by "B"
        units = {"GB": 1024 ** 3, "MB": 1024 ** 2, "KB": 1024, "B": 1}
        for unit, factor in units.items():
            if s.endswith(unit):
                return int(float(s[: -len(unit)]) * factor)
        return int(s)

    @staticmethod
    def _format_size(size):
        """Format a byte count as a human-readable string."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}TB"

    def _load_gitignore(self):
        gitignore_path = Path(".gitignore")
        if not gitignore_path.exists():
            return GitIgnoreSpec([])
        with gitignore_path.open("r") as f:
            return GitIgnoreSpec.from_lines(f)

    def _should_ignore(self, path, spec):
        git_style_path = path.relative_to(Path.cwd()).as_posix()
        if path.is_dir():
            git_style_path += "/"
        return spec.match_file(git_style_path)

    def _write_config_to_zip(self, zip_file: zipfile.ZipFile) -> None:
        config_content = yaml.dump(self.cfg.to_dict())
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=UserWarning)
            # Store the runtime-resolved config under a separate name so it
            # does not collide with the original config file in the archive.
            zip_file.writestr(".dlwheel-config.yaml", config_content)

    def _create_backup_zip(self):
        ignore_spec = self._load_gitignore()
        backup_abs = self.backup_dir.resolve()
        zip_path = self.backup_dir / "backup.zip"
        skipped_large = []

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in Path.cwd().rglob("*"):
                file_abs = file_path.resolve()

                if file_abs == backup_abs or backup_abs in file_abs.parents:
                    continue
                if self._should_ignore(file_path, ignore_spec):
                    continue
                # Skip common virtual-env directories not caught by .gitignore
                rel = file_path.relative_to(Path.cwd()).as_posix()
                if rel.startswith(".venv/") or rel == ".venv":
                    continue
                # Skip other experiment logs
                if rel.startswith("log/") or rel == "log":
                    continue
                # Skip git repository metadata
                if rel.startswith(".git/") or rel == ".git":
                    continue
                # Skip user-defined exclude patterns
                if self.exclude_spec.match_file(rel + "/" if file_path.is_dir() else rel):
                    continue
                if not file_path.is_file():
                    continue

                # Size check
                file_size = file_path.stat().st_size
                if file_size > self.max_file_size:
                    skipped_large.append((rel, file_size))
                    continue

                arcname = file_path.relative_to(Path.cwd())
                zipf.write(file_path, arcname)

            self._write_config_to_zip(zipf)

        # Report skipped large files
        if skipped_large:
            print(
                f"\n⚠️  The following files exceed {self._format_size(self.max_file_size)} and were skipped:"
            )
            for name, size in skipped_large:
                print(f"  - {name} ({self._format_size(size)})")
            print()
