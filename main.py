import logging
import asyncio
import os  # Додай цей імпорт
from aiogram import Bot, Dispatcher, types, executor
from aiohttp import web

# Тепер бот бере токен зі змінних оточення Render
TOKEN = os.getenv('BOT_TOKEN')

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN, parse_mode="Markdown")
dp = Dispatcher(bot)

ALIASES = {
    "test": 440640603, # Без лапок!
}

# Магія для Render, щоб він не бачив Failed
async def handle(request):
    return web.Response(text="Lumia is alive!")

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.reply(f"Люмія ожила! Твій ID: `{message.chat.id}`")

@dp.message_handler(commands=['shout'], content_types=types.ContentTypes.ANY)
async def shout_handler(message: types.Message):
    args = message.get_args().split(maxsplit=1)
    if not args:
        return await message.reply("Куди кричати? Приклад: `/shout test текст`")
    
    alias = args[0]
    text = args[1] if len(args) > 1 else ""
    target_id = ALIASES.get(alias, alias)

    info = f"🗣 **КРИК З ЧАТУ:** {message.chat.title or 'Приват'}\n👤 **Від:** {message.from_user.full_name}\n\n"

    try:
        await bot.send_message(target_id, info + text)
        await message.reply("Полетіло! 🚀")
    except Exception as e:
        await message.reply(f"Помилка: {e}")

if __name__ == '__main__':
    # Створюємо міні-сервер для Render на порту 10000
    app = web.Application()
    app.router.add_get('/', handle)
    
    # Запускаємо і бота, і сервер одночасно
    loop = asyncio.get_event_loop()
    loop.create_task(executor.start_polling(dp, skip_updates=True))
    web.run_app(app, port=10000)
