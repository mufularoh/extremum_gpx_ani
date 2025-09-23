import enum
import asyncio
from pathlib import Path
from typing import Union
import gpxpy
import gpxpy.gpx

from settings import Settings
from uuid import uuid1


class AnimationResult(enum.Enum):
    Error = enum.auto()
    Success = enum.auto()

async def animate_tracks(settings: Settings, files: list[Path]) -> tuple[AnimationResult, Union[str, Path]]:
    actual_files: list[Path] = []
    waypoints: list[gpxpy.gpx.GPXWaypoint] = []
    for f in files:
        parsed = gpxpy.parse(f.read_text())
        if parsed.tracks:
            actual_files.append(f)
        elif parsed.waypoints:
            waypoints += parsed.waypoints
    if waypoints:
        if not actual_files:
            return AnimationResult.Error, "Нет файлов, содержащих треки!"
        to_enhance = actual_files[0]
        writer = gpxpy.parse(to_enhance.read_text())
        for wp in waypoints:
            writer.waypoints.append(wp)
        to_enhance.write_text(writer.to_xml())
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
        ["--input", actual_files[i].resolve().absolute().as_posix(), "--color", colors[i]]
        for i, _ in enumerate(actual_files)
    ], [])
    proc = await asyncio.create_subprocess_exec(
        *command, 
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    if False:
        print(stdout.decode())
        print(stderr.decode())
    if not destination.exists():
        return AnimationResult.Error, stderr.decode()
    return AnimationResult.Success, destination


