import asyncio
from pathlib import Path
from aiogram.utils.keyboard import InlineKeyboardBuilder
from download import load_file
from files import AnimationResult, animate_tracks
from settings import Settings
from bot import get_bot


from aiogram import Dispatcher
from aiogram.filters import Command, CommandStart
from aiogram.types import BotCommand, FSInputFile, InlineKeyboardButton, Message, WebAppInfo

from storage import OnAddTrack, TracksStorage
from utils import MessageType, debug_output

dp = Dispatcher()
settings = Settings.load()
cropper_info = WebAppInfo(url=settings.app_location)
bot = get_bot(settings.api_token)

@dp.message(CommandStart())
async def start_command_handler(message: Message):
    await message.answer(
        "Привет!\nЯ - бот который может заанимировать твои треки с тренировок 🐕‍🦺\nОтветь мне, " \
        "приложив треки тренировки к сообщению, и, когда все треки загрузятся, нажми \"📽️ Анимировать\" в моём меню!"
    )

@dp.message(Command("list_tracks"))
async def list_command_handler(message: Message):
    tracks = TracksStorage.list_tracks(message.chat.id)
    builder = InlineKeyboardBuilder([[
        InlineKeyboardButton(text="Обрезать трек", web_app=cropper_info)
    ]])
    if tracks:
        text = "\n".join([track.file_name for track in tracks])
        await message.answer("Загруженные треки:\n" + text, reply_markup=builder.as_markup())
    else:
        await message.answer("Треков нет!")

@dp.message(Command("clear_tracks"))
async def clear_command_handler(message: Message):
    TracksStorage.clear_tracks(message)
    debug_output("Tracks cleared", MessageType.Info)
    await message.answer("Треки очищены!")

@dp.message(Command("animate"))
async def animate_command_handler(message: Message):
    global bot
    global settings
    tracks = TracksStorage.list_tracks(message.chat.id)
    if not tracks:
        await message.answer("Треки не загружены! Приложи их к сообщению")
        return
    
    await message.answer("Анимирую треки, пришлю результат как только он будет готов!")
    files: list[Path] = []
    for track in tracks:
        downloaded = await load_file(bot, track.document_id, track.unique_id)
        files.append(downloaded)
    video_status, value = await animate_tracks(settings, files)
    if video_status == AnimationResult.Error:
        await bot.send_message(message.chat.id, f"Ошибка: {value}")
        return
    await bot.send_message(message.chat.id, "Анимация готова!")
    assert isinstance(value, Path)
    uploaded = FSInputFile(value)
    await bot.send_document(message.chat.id, uploaded)
    TracksStorage.clear_tracks(message)
    await bot.send_message(message.chat.id, "Треки очищены!")

    



@dp.message()
async def message_handler(message: Message):
    result, val = TracksStorage.try_add_track(message)
    if result == OnAddTrack.NoDocument:
        await message.answer("Пожалуйста, приложи GPX-трек!")
        debug_output("No attach", MessageType.Error)
    elif result == OnAddTrack.NotGPX:
        debug_output("Wrong mime", MessageType.Error)
        await message.answer(f"Пожалуйста, приложи именно GPX-трек :) (сейчас: {val})")
    elif result == OnAddTrack.TooMany:
        # Shouldn't happen
        debug_output("Too many tracks", MessageType.Error)
        await message.answer(f"Уже загружено {val} треков. Точно это всё нужно запихать в одну анимацию? Почисти, пожалуйста, ненужное!")
    elif result == OnAddTrack.Success:
        debug_output("Track added", MessageType.Info)
        await message.answer(f"Файл {val} добавлен в анимацию")
    

async def main() -> None:
    global bot 
    await bot.set_my_commands([
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="list_tracks", description="Список загруженных треков"),
        BotCommand(command="clear_tracks", description="Очистить загруженные треки"),
        BotCommand(command="animate", description="📽️ Анимировать")
    ])
    debug_output("Started bot", MessageType.Success)
    await dp.start_polling(bot)




if __name__ == "__main__":
    asyncio.run(main())
