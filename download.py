from pathlib import Path
from aiogram import Bot

def get_file_path(unique_id: str) -> Path:
    base = Path("./files")
    if not base.exists():
        base.mkdir()
    return base / f"{unique_id}.gpx"

async def load_file(bot: Bot, document_id: str, unique_id: str) -> Path:
    base = Path("./files")
    if not base.exists():
        base.mkdir()

    destination = base / f"{unique_id}.gpx"
    if not destination.exists():
        await bot.download(document_id, destination)
    return destination
