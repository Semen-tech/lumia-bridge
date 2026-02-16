import logging
import asyncio
import os
import json
from aiogram import Bot, Dispatcher, types, executor
from aiohttp import web
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent

# Налаштування
TOKEN = os.getenv('BOT_TOKEN')
DB_FILE = "aliases.json"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

@dp.inline_handler()
async def inline_shout(inline_query: InlineQuery):
    results = []
    # Проходимо по твоїх збережених аліасах
    for name, chat_id in aliases.items():
        results.append(
            InlineQueryResultArticle(
                id=str(chat_id),
                title=f"Крикнути в: {name}",
                description=f"Натисни, щоб підготувати команду для {name}",
                input_message_content=InputTextMessageContent(
                    f"/shout {name} " # Вставляє це в поле набору
                )
            )
        )
    
    await bot.answer_inline_query(inline_query.id, results=results, cache_time=1)

# Завантаження аліасів
def load_aliases():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {"test": 440640603} # Твій дефолтний ID

aliases = load_aliases()

def save_aliases():
    with open(DB_FILE, "w") as f:
        json.dump(aliases, f)

# Магія підказок при наборі
async def set_commands():
    commands = [
        types.BotCommand("shout", "Крикнути в чат: /shout [аліас] [текст]"),
        types.BotCommand("save_alias", "Зберегти цей чат: /save_alias [назва]"),
        types.BotCommand("list", "Показати всі доступні чати")
    ]
    await bot.set_my_commands(commands)

# Web-server для Render
async def handle(request):
    return web.Response(text="Lumia 2.0 is sparkling!")

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    # Використовуємо HTML тег <code> замість бектіків
    await message.reply(
        f"Люмія 2.0 на зв'язку! Твій ID: <code>{message.chat.id}</code>\n"
        "Використовуй /save_alias, щоб додати цей чат."
    )

@dp.message_handler(commands=['save_alias'])
async def cmd_save_alias(message: types.Message):
    args = message.get_args().strip()
    if not args:
        return await message.reply("Назви аліас! Приклад: `/save_alias work`")
    
    aliases[args] = message.chat.id
    save_aliases()
    await message.reply(f"✅ Збережено! Тепер я знаю цей чат як `{args}`")

@dp.message_handler(commands=['list'])
async def cmd_list(message: types.Message):
    text = "📍 **Доступні чати:**\n" + "\n".join([f"• `{k}`" for k in aliases.keys()])
    await message.reply(text)

@dp.message_handler(commands=['shout'])
async def shout_handler(message: types.Message):
    args = message.get_args().split(maxsplit=1)
    if len(args) < 2:
        return await message.reply("Мало інформації! Треба: /shout [аліас] [текст]")

    alias, text = args[0], args[1]
    target_id = aliases.get(alias)

    if not target_id:
        return await message.reply(f"Хто такий {alias}? Я його не знаю. Спробуй /list")

    sender = message.from_user.full_name
    source = message.chat.title or "Приват"

    # Гарне оформлення через HTML
    header = f"🗣 <b>КРИК З:</b> {source}\n👤 <b>Від:</b> {sender}\n\n"

    try:
        await bot.send_message(target_id, header + text)
        await message.reply(f"Полетіло в <b>{alias}</b>! 🚀")
    except Exception as e:
        await message.reply(f"Не можу докричатися: {e}")
    
    alias, text = args[0], args[1]
    target_id = aliases.get(alias)

    if not target_id:
        return await message.reply(f"Хто такий `{alias}`? Я його не знаю. Спробуй /list")

    sender = message.from_user.full_name
    source = message.chat.title or "Приват"
    
    header = f"🗣 **КРИК З:** {source}\n👤 **Від:** {sender}\n\n"
    
    try:
        await bot.send_message(target_id, header + text)
        await message.reply(f"Полетіло в `{alias}`! 🚀")
    except Exception as e:
        await message.reply(f"Не можу докричатися: {e}")

if __name__ == '__main__':
    app = web.Application()
    app.router.add_get('/', handle)
    
    loop = asyncio.get_event_loop()
    loop.create_task(set_commands()) # Встановлюємо підказки
    loop.create_task(executor.start_polling(dp, skip_updates=True))
    web.run_app(app, port=10000)
