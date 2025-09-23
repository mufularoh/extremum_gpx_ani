from pathlib import Path

import json
from dataclasses import dataclass
from typing import Self



@dataclass
class Settings:
    api_token: str
    animator_executable: list[str]
    animator_params: list[str]
    app_location: str

    @classmethod
    def load(cls) -> Self:
        p = Path("./config.json")
        in_docker = Path("./__in_docker").exists()

        if not p.exists():
            print("Please define config.json based on config_sample.json")
            exit(1)
        with p.open("r") as f:
            data = json.load(f)
            if in_docker:
                executor = ["java", "-jar", "/app/animator.jar"]
            else:
                executor = data["animator_executable"]
            try:
                return cls(
                    api_token=data["api_token"],
                    animator_executable=executor,
                    animator_params=data["animator_params"],
                    app_location=data["app_location"]
                )
            except KeyError:
                 print("Please make sure that all fields from config_sample.json are set in config.json")
                 exit(1)
