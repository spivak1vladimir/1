import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from vkbottle.bot import Bot, Message

# ---------------- НАСТРОЙКИ ----------------
VK_TOKEN = "vk1.a.VNTxYTHvQMbbRQFFZyY7575TCJrJSYPN4CxIBc9u-PdamXSD0-iy2BDOBtkviwfC-BNtnE1qwEraCM-USWlrvf6arvuGcSgd2qeY9KaUCecbJyQklhgiKhvJYz8b8q9GxBei_52VN4UDjsKGLGWI1w7h7Ensf7MzeonRguZfGdY41Oc6tBx-nJSB8IKRv4xYvlyLf39ieMJl1iF0zjWXdA"
ADMIN_ID = 194614510
MAX_SLOTS = 15
DATA_FILE = "registered_users_sunday_vk.json"

RUN_DATETIME = datetime(2026, 3, 23, 11, 0)
RUN_DATE_TEXT = "23.03.26"
RUN_TITLE_TEXT = "Воскресный забег — Cosmic latte, Москва"
START_POINT = "Cosmic latte, кофейня, Якиманский пер., 6, стр. 1, Москва"
START_MAP_LINK_10KM = "https://yandex.ru/maps/-/CPufVPIR"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- ДАННЫЕ ----------------
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        registered_users = json.load(f)
        if not isinstance(registered_users, list):
            registered_users = []
else:
    registered_users = []

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(registered_users, f, ensure_ascii=False, indent=2)

def build_info_text():
    text = f"{RUN_DATE_TEXT}\n{RUN_TITLE_TEXT}\n\nСтарт: {START_POINT}\nСбор: 10:30\nСтарт: 11:00\n\nМаршрут 10 км:\n{START_MAP_LINK_10KM}\n\nУчастники ({len(registered_users)}):\n"
    if not registered_users:
        text += "— пока нет участников"
    else:
        for i, u in enumerate(registered_users, start=1):
            username = f"{u['username']}" if u["username"] else "—"
            text += f"{i}. {u['name']} {username}\n"
    return text

# ---------------- РУЧНАЯ КЛАВИАТУРА ----------------
def main_keyboard():
    return {
        "one_time": False,
        "buttons": [
            [
                {"action": {"type": "text", "label": "Регистрация"}, "color": "positive"},
                {"action": {"type": "text", "label": "Отменить регистрацию"}, "color": "negative"}
            ],
            [
                {"action": {"type": "text", "label": "Информация о забеге"}, "color": "primary"}
            ]
        ]
    }

# ---------------- БОТ ----------------
bot = Bot(token=VK_TOKEN)

# ---------------- ХЭНДЛЕРЫ ----------------
@bot.on.message(text="Регистрация")
async def register_user(message: Message):
    user_id = message.from_id
    if any(u["id"] == user_id for u in registered_users):
        await message.answer(build_info_text(), keyboard=main_keyboard())
        return
    if len(registered_users) >= MAX_SLOTS:
        await message.answer("Все места заняты.", keyboard=main_keyboard())
        return
    user_data = {"id": user_id, "name": str(user_id), "username": str(user_id)}
    registered_users.append(user_data)
    save_data()
    await bot.api.messages.send(peer_id=ADMIN_ID, message=f"Новый участник воскресного забега\nID: {user_id}", random_id=0)
    await message.answer("Вы зарегистрированы на воскресный забег!", keyboard=main_keyboard())

@bot.on.message(text="Отменить регистрацию")
async def cancel_user(message: Message):
    user_id = message.from_id
    for u in registered_users:
        if u["id"] == user_id:
            registered_users.remove(u)
            save_data()
            await bot.api.messages.send(peer_id=ADMIN_ID, message=f"Участник отменил регистрацию\nID: {user_id}", random_id=0)
            break
    await message.answer("Регистрация отменена.", keyboard=main_keyboard())

@bot.on.message(text="Информация о забеге")
async def info(message: Message):
    await message.answer(build_info_text(), keyboard=main_keyboard())

# ---------------- НАПОМИНАНИЕ ----------------
async def send_reminder():
    text = f"{RUN_DATE_TEXT}\n{RUN_TITLE_TEXT}\n\nЗавтра воскресный забег.\n\nСтарт: {START_POINT}\nСбор: 10:30\nСтарт: 11:00\n\nМаршрут 10 км:\n{START_MAP_LINK_10KM}"
    for u in registered_users:
        try:
            await bot.api.messages.send(peer_id=u["id"], message=text, random_id=0)
        except:
            pass
    await bot.api.messages.send(peer_id=ADMIN_ID, message=f"Напоминание отправлено.\nВсего участников: {len(registered_users)}", random_id=0)

# ---------------- JOB ----------------
async def reminder_scheduler():
    while True:
        now = datetime.now()
        reminder_time = RUN_DATETIME - timedelta(hours=24)
        if now >= reminder_time and now < reminder_time + timedelta(minutes=1):
            await send_reminder()
            await asyncio.sleep(60)
        else:
            await asyncio.sleep(30)

# ---------------- ЗАПУСК ----------------
async def start_bot():
    asyncio.create_task(reminder_scheduler())
    await bot.run_polling()

# ---------------- ПРОВЕРКА LOOP ----------------
try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = None

if loop and loop.is_running():
    asyncio.create_task(start_bot())  # loop уже есть → создаём задачу
else:
    asyncio.run(start_bot())          # loop нет → запускаем через asyncio.run
