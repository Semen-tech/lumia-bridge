import logging
from aiogram import Bot, Dispatcher, types, executor

TOKEN = '8428334603:AAE72CDCWMDzy1yCSWIQxsP3hnwp2Ssdk2s'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN, parse_mode="Markdown")
dp = Dispatcher(bot)

# Сюди будеш додавати аліаси: "назва": ID_групи
ALIASES = {
    "test": 440640603, 
}

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.reply(f"Люмія на зв'язку! ID чату: `{message.chat.id}`")

@dp.message_handler(commands=['shout'], content_types=types.ContentTypes.ANY)
async def shout_handler(message: types.Message):
    args = message.get_args().split(maxsplit=1)
    if not args:
        return await message.reply("Куди кричати? Треба: `/shout аліас текст`")

    alias = args[0]
    text = args[1] if len(args) > 1 else ""
    target_id = ALIASES.get(alias, alias)

    info = f"🗣 **КРИК З ЧАТУ:** {message.chat.title}\n👤 **Від:** {message.from_user.full_name}\n\n"

    try:
        # Якщо є реплай на медіа (фото/стікер/відео)
        if message.reply_to_message:
            await bot.copy_message(target_id, message.chat.id, message.reply_to_message.message_id, caption=info + text)
        else:
            await bot.send_message(target_id, info + text)
        await message.reply("Доставлено! 🚀")
    except Exception as e:
        await message.reply(f"Упс: {e}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
