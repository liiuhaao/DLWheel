import argparse
import time
from pathlib import Path

import yaml
from box import Box

from dlwheel.utils import get_timestamp_name


class ConfigLoader:
    def __init__(self):
        self._cfg = Box(default_box=True, default_box_attr=None, box_dots=True)

    def run(self):
        args = self._parse_args()
        self._load_config(args.config)
        self._overide_config(args)
        return self._cfg

    def _parse_args(self):
        parser = argparse.ArgumentParser(allow_abbrev=False)
        parser.add_argument("--config", default="config/default.yaml")
        parser.add_argument("--backup", action="store_true", default=argparse.SUPPRESS)
        parser.add_argument("--resume", action="store_true", default=argparse.SUPPRESS)
        parser.add_argument("--name", default=get_timestamp_name())
        parser.add_argument("--tmp", action="store_true", default=argparse.SUPPRESS)

        args, unk = parser.parse_known_args()

        if getattr(args, "tmp", False):
            args.name = "_tmp"

        for arg in unk:
            k, _, v = arg.lstrip("-").partition("=")
            setattr(args, k, v if _ else True)
        return args

    def _load_config(self, config_path):
        if Path(config_path).exists():
            yaml_cfg = yaml.load(open(config_path), yaml.FullLoader)
            self._cfg.update(yaml_cfg)

    def _overide_config(self, args):
        for key, value in vars(args).items():
            *path, key = key.split(".")
            current = self._cfg
            for p in path:
                if not isinstance(current.get(p), (Box, dict)):
                    current[p] = Box(
                        default_box=True, default_box_attr=None, box_dots=True
                    )
                current = current[p]
            origin = current.get(key)
            # If CLI passes a bare True (e.g. --backup) and the YAML already
            # holds a dict-like value, treat it as "enable" without destroying
            # the existing sub-config.
            if value is True and isinstance(origin, (Box, dict)):
                continue
            current[key] = self._convert(value, origin)

    def _convert(self, value, origin):
        try:
            return type(origin)(value) if origin else value
        except:
            return value
