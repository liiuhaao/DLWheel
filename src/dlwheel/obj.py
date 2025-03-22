import copy
from collections.abc import MutableMapping
from types import SimpleNamespace
from typing import Any, Iterator


class Obj(SimpleNamespace, MutableMapping):

    def __init__(self, **kwargs: Any):
        super().__init__()
        self._convert_and_set(kwargs)

    def _convert_value(self, value: Any) -> Any:
        if isinstance(value, dict):
            return Obj(**value)
        if isinstance(value, list):
            return [self._convert_value(v) for v in value]
        return value

    def _convert_and_set(self, data: dict) -> None:
        for k, v in data.items():
            self.__dict__[k] = self._convert_value(v)

    def __getitem__(self, key: str) -> Any:
        return self.__dict__[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.__dict__[key] = self._convert_value(value)

    def __delitem__(self, key: str) -> None:
        del self.__dict__[key]

    def __iter__(self) -> Iterator:
        return iter(self.__dict__)

    def __len__(self) -> int:
        return len(self.__dict__)

    def __getattr__(self, name: str) -> Any:
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
        return None

    def to_dict(self) -> dict:
        def _convert(obj: Any) -> Any:
            if isinstance(obj, Obj):
                return {k: _convert(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_convert(v) for v in obj]
            return obj

        return _convert(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Obj":
        return cls(**data)

    def __str__(self) -> str:
        return self.__repr__()

    def keys(self):
        return self.__dict__.keys()

    def __contains__(self, key: object) -> bool:
        return key in self.__dict__

    def to(self, device: str) -> "Obj":
        import torch

        def _move(obj: Any) -> Any:
            if isinstance(obj, torch.Tensor):
                return obj.to(device)
            if isinstance(obj, Obj):
                return obj.to(device)
            if isinstance(obj, list):
                return [_move(v) for v in obj]
            return obj

        for k, v in self.items():
            self[k] = _move(v)
        return self

    def __deepcopy__(self, memo: dict) -> "Obj":
        new_obj = self.__class__()
        memo[id(self)] = new_obj
        for k, v in self.__dict__.items():
            new_obj.__dict__[k] = copy.deepcopy(v, memo)
        return new_obj
