import logging
import asyncio
import os
import json
import aiohttp
from aiogram import Bot, Dispatcher, types, executor
from aiohttp import web

# Налаштування
TOKEN = os.getenv('BOT_TOKEN')
APP_URL = os.getenv('APP_URL') # Твоє посилання на Render
DB_FILE = "aliases.json"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

# --- РОБОТА З БАЗОЮ ДАНИХ (JSON) ---
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading DB: {e}")
    return {"test": 440640603} # Дефолтний аліас (твій ID)

aliases = load_db()

def save_db():
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(aliases, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logging.error(f"Error saving DB: {e}")

# --- АНТИ-СОН ---
async def keep_alive():
    if not APP_URL:
        logging.warning("APP_URL not set! Anti-sleep disabled.")
        return
    while True:
        await asyncio.sleep(300) # 5 хвилин
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(APP_URL) as resp:
                    logging.info(f"Ping {APP_URL}: status {resp.status}")
        except Exception as e:
            logging.error(f"Ping failed: {e}")

# --- INLINE MODE (Підказки) ---
@dp.inline_handler()
async def inline_handler(query: types.InlineQuery):
    results = []
    user_input = query.query.strip()

    # КРОК 1: Вибір аліасу
    if not user_input:
        for name in aliases.keys():
            results.append(
                types.InlineQueryResultArticle(
                    id=f"select_{name}",
                    title=f"📁 Обрати чат: {name}",
                    description="Натисни, щоб підготувати команду",
                    # В aiogram 2.x назва аргументу саме така:
                    switch_inline_query_current_chat=f"shout {name} ",
                    # Обов'язкове поле, хоча switch його перекриє
                    input_message_content=types.InputTextMessageContent(f"Обрано {name}")
                )
            )
    
    # КРОК 2: Введення тексту
    elif user_input.startswith("shout "):
        parts = user_input.split(maxsplit=2)
        if len(parts) >= 3:
            alias_name, shout_text = parts[1], parts[2]
            results.append(
                types.InlineQueryResultArticle(
                    id="send_final",
                    title="🚀 НАДІСЛАТИ КРИК",
                    description=f"В чат: {alias_name} | Текст: {shout_text}",
                    input_message_content=types.InputTextMessageContent(
                        f"/shout {alias_name} {shout_text}"
                    )
                )
            )
        else:
            results.append(
                types.InlineQueryResultArticle(
                    id="waiting",
                    title="📝 Друкуй повідомлення...",
                    switch_inline_query_current_chat=user_input,
                    input_message_content=types.InputTextMessageContent("Очікую текст...")
                )
            )

    await query.answer(results, cache_time=1, is_personal=True)
    
# --- ОБРОБНИКИ КОМАНД ---
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.reply(
        "<b>Lumia Bridge</b> active.\n"
        f"Your ID: <code>{message.chat.id}</code>\n"
        "Use /save_alias [name] to add this chat."
    )

@dp.message_handler(commands=['save_alias'])
async def cmd_save(message: types.Message):
    name = message.get_args().strip()
    if not name:
        return await message.reply("Provide a name: <code>/save_alias group_name</code>")
    
    aliases[name] = message.chat.id
    save_db()
    await message.reply(f"✅ Alias <b>{name}</b> saved for this chat!")

@dp.message_handler(commands=['shout'])
async def cmd_shout(message: types.Message):
    args = message.get_args().split(maxsplit=1)
    if len(args) < 2:
        return await message.reply("Format: <code>/shout [alias] [text]</code>")
    
    alias, text = args[0], args[1]
    target_id = aliases.get(alias)
    
    if not target_id:
        return await message.reply(f"Unknown alias: <b>{alias}</b>")
    
    header = f"🗣 <b>FROM:</b> {message.from_user.full_name}\n\n"
    try:
        await bot.send_message(target_id, header + text)
        await message.reply("Sent! 🚀")
    except Exception as e:
        await message.reply(f"Delivery failed: {e}")

# --- WEB SERVER FOR RENDER ---
async def web_handle(request):
    return web.Response(text="Lumia is alive. 🍸")

if __name__ == '__main__':
    app = web.Application()
    app.router.add_get('/', web_handle)
    
    loop = asyncio.get_event_loop()
    loop.create_task(keep_alive())
    
    # Встановлюємо команди в меню
    loop.run_until_complete(bot.set_my_commands([
        types.BotCommand("shout", "Send message via alias"),
        types.BotCommand("save_alias", "Save current chat as alias")
    ]))
    
    executor.start_polling(dp, skip_updates=True)
