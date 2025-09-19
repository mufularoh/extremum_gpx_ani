from pathlib import Path

import json
from dataclasses import dataclass
from typing import Self

from utils import MessageType, debug_output


@dataclass
class Settings:
    api_token: str
    animator_executable: list[str]
    animator_params: list[str]

    @classmethod
    def load(cls) -> Self:
        p = Path("./config.json")
        if not p.exists():
            debug_output("Please define config.json based on config_sample.json", MessageType.Error)
            exit(1)
        with p.open("r") as f:
            data = json.load(f)
            try:
                return cls(
                    api_token=data["api_token"],
                    animator_executable=data["animator_executable"],
                    animator_params=data["animator_params"]
                )
            except KeyError:
                 debug_output("Please make sure that all fields from config_sample.json are set in config.json", MessageType.Error)
                 exit(1)
