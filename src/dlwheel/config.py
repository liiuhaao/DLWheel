import argparse
import time
from pathlib import Path

import yaml
from box import Box


class ConfigLoader:
    def __init__(self):
        self._cfg = Box(default_box=True, default_box_attr=None, box_dots=True)

    def run(self):
        args = self._parse_args()
        self._load_config(args.config)
        self._overide_config(args)
        return self._cfg

    def _parse_args(self):
        p = argparse.ArgumentParser(allow_abbrev=False)
        p.add_argument("--config", default="config/default.yaml")
        p.add_argument("--backup", action="store_true")
        p.add_argument("--name", default=time.strftime("%y%m%d%H%M%S"))
        args, unk = p.parse_known_args()
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
                if current[p] is None:
                    current[p] = Box(default_box=True, default_box_attr=None, box_dots=True)
                current = current[p]
            current[key] = self._convert(value, current.get(key))

    def _convert(self, value, origin):
        try:
            return type(origin)(value) if origin else value
        except:
            return value
