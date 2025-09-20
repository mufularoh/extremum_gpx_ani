import enum
import asyncio
from pathlib import Path
from typing import Union

from settings import Settings
from uuid import uuid1


class AnimationResult(enum.Enum):
    Error = enum.auto()
    Success = enum.auto()

async def animate_tracks(settings: Settings, files: list[Path]) -> tuple[AnimationResult, Union[str, Path]]:
    colors = [
        "#1b5e20",
        "#880e4f",
        "#bf360c",
        "#4e342e",
        "#01579b",
        "#1a237e",
        "#ff6f00",
        "#455a64",
        "#33691e",
        "#ff0000"
    ]
    base = Path("./files/")
    if not base.exists():
        base.mkdir()
    destination = base / f"{uuid1().hex}.mp4"
    command = settings.animator_executable + settings.animator_params + [
        "--output", destination.resolve().absolute().as_posix()
    ] + sum([
        ["--input", files[i].resolve().absolute().as_posix(), "--color", colors[i]]
        for i, _ in enumerate(files)
    ], [])
    proc = await asyncio.create_subprocess_exec(
        *command, 
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    _, stderr = await proc.communicate()
    if not destination.exists():
        return AnimationResult.Error, stderr.decode()
    return AnimationResult.Success, destination


