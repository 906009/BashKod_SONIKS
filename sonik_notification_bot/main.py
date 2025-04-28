import asyncio
from datetime import datetime
import logging
import sys
import requests
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message
import json
from pathlib import Path

TOKEN = "7571048547:AAFVXKIj4vtm454s3CfHpXgwUpp5hOmKZiI"
dp = Dispatcher()
REMINDERS_FILE = Path("reminders.json")
reminders = []


def load_reminders():
    if REMINDERS_FILE.exists():
        with open(REMINDERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            for item in data:
                iso_time = item["remind_time"].rstrip("Z")
                item["remind_time"] = datetime.fromisoformat(iso_time)
            return data
    return []


def save_reminders():
    with open(REMINDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(
            [
                {"user_id": r["user_id"], "id_obs": r["id_obs"],
                 "remind_time": r["remind_time"].isoformat(timespec="microseconds") + "Z"}
                for r in reminders
            ],
            f,
            indent=2,
            ensure_ascii=False
        )


async def schedule():
    global reminders
    while True:
        try:
            reminders = load_reminders()
            now = datetime.utcnow()
            for reminder in list(reminders):
                if now >= reminder["remind_time"]:
                    try:
                        await bot.send_message(
                            reminder["user_id"],
                            f"*Напоминание!*\nНачинается наблюдение ID: {reminder['id_obs']}", parse_mode="Markdown"
                        )
                    except:
                        pass
                    reminders.remove(reminder)
                    save_reminders()
            await asyncio.sleep(10)
        except:
            pass


async def add_reminder(message, payload):
    try:
        url = f"https://sonik.space/api/observations/?id={payload}&status=future"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data != []:
                remind_time_str = None
                for dat in data:
                    remind_time_str = dat['start']
                if remind_time_str:
                    remind_time = datetime.fromisoformat(remind_time_str.rstrip("Z"))
                    reminder = {
                        "user_id": message.from_user.id,
                        "id_obs": payload,
                        "remind_time": remind_time,
                    }
                    reminders.append(reminder)
                    save_reminders()

                    await message.answer(f"Мы уведомим вас при начале наблюдения.\n"
                                         f"ID: {payload}, напомним в {remind_time.strftime('%Y-%m-%d %H:%M')} UTC")
            else:
                await message.answer(f"Вероятно данное наблюдение уже произошло.")
    except:
        await message.answer(
            "Ошибка!\nНеверный аргумент.",
            parse_mode="Markdown"
        )


@dp.message(CommandStart(deep_link=True))
async def command_start_handler(message: Message, command: CommandObject) -> None:
    args = command.args
    # payload = decode_payload(args)
    payload = args
    if payload.startswith('ID_OBS='):
        payload = payload[7:]
        await add_reminder(message, payload)
    else:
        await message.answer(f"Привет, *{message.from_user.username}*!\n"
                             f"Данный бот будет уведомлять тебя о начале пролёта спутника над станцией.\n"
                             f"Отсканируй QR-код желаемого пролёта и бот оповестит тебя.", parse_mode="Markdown")


async def main() -> None:
    global bot
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    asyncio.create_task(schedule())
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
