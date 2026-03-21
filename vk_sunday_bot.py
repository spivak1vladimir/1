import os
import json
import asyncio
from vkbottle.bot import Bot, Message
from vkbottle import Keyboard, KeyboardButtonColor

# ---------------- НАСТРОЙКИ ----------------
VK_TOKEN = "vk1.a.VNTxYTHvQMbbRQFFZyY7575TCJrJSYPN4CxIBc9u-PdamXSD0-iy2BDOBtkviwfC-BNtnE1qwEraCM-USWlrvf6arvuGcSgd2qeY9KaUCecbJyQklhgiKhvJYz8b8q9GxBei_52VN4UDjsKGLGWI1w7h7Ensf7MzeonRguZfGdY41Oc6tBx-nJSB8IKRv4xYvlyLf39ieMJl1iF0zjWXdA"
ADMIN_ID = 194614510
MAX_SLOTS = 15
DATA_FILE = "/app/data/registered_users_sunday_vk.json"

bot = Bot(token=VK_TOKEN)

# ---------------- ДАННЫЕ ----------------
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        registered_users = json.load(f)
else:
    registered_users = []

def save_data():
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(registered_users, f, ensure_ascii=False, indent=2)

def main_keyboard():
    kb = Keyboard(one_time=False)
    kb.add("Регистрация", color=KeyboardButtonColor.POSITIVE)
    kb.add("Отменить регистрацию", color=KeyboardButtonColor.NEGATIVE)
    kb.row()
    kb.add("Информация о забеге", color=KeyboardButtonColor.PRIMARY)
    return kb.get_json()

def build_info_text():
    text = f"Участники ({len(registered_users)}):\n"
    if not registered_users:
        text += "— пока нет участников"
    else:
        for i, u in enumerate(registered_users, start=1):
            text += f"{i}. {u['id']}\n"
    return text

# ---------------- ХЭНДЛЕРЫ ----------------
@bot.on.message(text="Регистрация")
async def register_user(message: Message):
    user_id = message.from_id
    if any(u["id"] == user_id for u in registered_users):
        await message.answer("Вы уже зарегистрированы!\n\n" + build_info_text(), keyboard=main_keyboard())
        return
    if len(registered_users) >= MAX_SLOTS:
        await message.answer("Все места заняты 😕", keyboard=main_keyboard())
        return
    registered_users.append({"id": user_id})
    save_data()
    await bot.api.messages.send(peer_id=ADMIN_ID, message=f"Новый участник зарегистрирован\nID: {user_id}", random_id=0)
    await message.answer("✅ Вы успешно зарегистрированы!", keyboard=main_keyboard())

@bot.on.message(text="Отменить регистрацию")
async def cancel_user(message: Message):
    user_id = message.from_id
    registered_users[:] = [u for u in registered_users if u["id"] != user_id]
    save_data()
    await message.answer("❌ Регистрация отменена.", keyboard=main_keyboard())

@bot.on.message(text="Информация о забеге")
async def info(message: Message):
    await message.answer(build_info_text(), keyboard=main_keyboard())

# ---------------- ЗАПУСК ----------------
async def main():
    await bot.run_polling()

try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = None

if loop and loop.is_running():
    asyncio.create_task(main())
else:
    asyncio.run(main())