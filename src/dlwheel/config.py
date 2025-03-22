import argparse
import time
from pathlib import Path

import yaml

from .obj import Obj


class ConfigLoader:
    def __init__(self):
        self._cfg = dict()
        self._args = None

    def run(self):
        args = self._parse_args()
        self._cfg.update(self._load_yaml(args.config))
        for key, value in vars(args).items():
            if key in self._cfg:
                try:
                    value = type(self._cfg[key])(value)
                except (ValueError, TypeError):
                    pass
            self._cfg[key] = value
        return Obj(**self._cfg)

    def _parse_args(self):
        parser = argparse.ArgumentParser(allow_abbrev=False)
        parser.add_argument("--config", type=str, default="config/default.yaml")
        parser.add_argument("--backup", action="store_true", default=False)
        parser.add_argument("--name", default=time.strftime("%y%m%d%H%M%S", time.localtime()), type=str)

        args, unknown_args = parser.parse_known_args()
        unknown_dict = {}
        for arg in unknown_args:
            if arg.startswith("--"):
                if "=" in arg:
                    key, value = arg.split("=", 1)
                    unknown_dict[key.lstrip("--")] = value
                else:
                    unknown_dict[arg.lstrip("--")] = True

        for key, value in unknown_dict.items():
            setattr(args, key, value)

        return args

    def _load_yaml(self, path):
        if not Path(path).exists():
            return dict()
            raise FileNotFoundError(f"Config file {path} not found")
        with open(path, "r") as f:
            return yaml.load(f, Loader=yaml.FullLoader)
