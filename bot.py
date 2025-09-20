from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode


def get_bot(api_token: str) -> Bot:
    return Bot(token=api_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
