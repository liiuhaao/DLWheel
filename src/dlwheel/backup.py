import os
import shutil
import subprocess
from pathlib import Path

import yaml
from pathspec import GitIgnoreSpec


class BackupSystem:

    def __init__(self, cfg):
        self.cfg = cfg
        log_path = cfg.path.log if cfg.path and cfg.path.log else f"log"
        self.backup_dir = Path(log_path) / cfg.name / "backup"

    def run(self):
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self._copy_project_files()
        self._export_environment()
        self._save_current_config()
        self._make_backup_readonly()

    def _export_environment(self):
        env_file = self.backup_dir / "environment.yml"
        with env_file.open("w") as f:
            subprocess.run(["conda", "env", "export"], stdout=f, check=True)

    def _load_gitignore(self) -> GitIgnoreSpec:
        gitignore_path = Path(".gitignore")
        if not gitignore_path.exists():
            return GitIgnoreSpec([])
        with gitignore_path.open("r") as f:
            return GitIgnoreSpec.from_lines(f)

    def _should_ignore(self, path: Path, spec: GitIgnoreSpec) -> bool:
        git_style_path = path.relative_to(Path.cwd()).as_posix()
        if path.is_dir():
            git_style_path += "/"
        return spec.match_file(git_style_path)

    def _copy_project_files(self):
        ignore_spec = self._load_gitignore()
        backup_abs = self.backup_dir.resolve()

        for item in Path.cwd().rglob("*"):
            item_abs = item.resolve()
            if item_abs == backup_abs or backup_abs in item_abs.parents:
                continue
            if self._should_ignore(item, ignore_spec):
                continue
            if item.is_dir():
                continue
            dest = self.backup_dir / item.relative_to(Path.cwd())
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dest)

    def _save_current_config(self):
        config_path = self.backup_dir / self.cfg.config
        config_path.parent.mkdir(exist_ok=True)
        with config_path.open("w") as f:
            yaml.dump(self.cfg.to_dict(), f)

    def _make_backup_readonly(self):
        for root, dirs, files in os.walk(self.backup_dir):
            os.chmod(root, 0o555)
            for name in files:
                file_path = Path(root) / name
                os.chmod(file_path, 0o444)  # 只读权限
