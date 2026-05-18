import os
import asyncio
from aiohttp import web
from telethon import TelegramClient, events
from telethon.sessions import StringSession

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

api_id = int(os.environ["API_ID"])
api_hash = os.environ["API_HASH"]
string_session = os.environ["STRING_SESSION"]

TARGET = os.environ["TARGET_CHANNEL"]

SOURCE = [
    x.strip().lstrip("@")
    for x in os.environ.get("SOURCE_CHATS", "").split(",")
    if x.strip()
]

client = TelegramClient(
    StringSession(string_session),
    api_id,
    api_hash,
    loop=loop
)

# ================= TELEGRAM =================
@client.on(events.NewMessage)
async def handler(event):
    chat = await event.get_chat()

    username = getattr(chat, "username", None)
    chat_id = str(event.chat_id)

    if username:
        username = username.lstrip("@")

    if username not in SOURCE and chat_id not in SOURCE:
        return

    text = event.message.message or ""

    if not (
        "youtube.com" in text
        or "youtu.be" in text
        or "music.yandex.ru" in text
    ):
        return

    if event.message.media:
        await client.send_file(TARGET, event.message.media, caption=text)
    else:
        await client.send_message(TARGET, text)

    print("✅ SENT")


# ================= WEB SERVER =================
async def handle(request):
    return web.Response(text="OK")


async def start_web():
    app = web.Application()
    app.router.add_get("/", handle)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.environ.get("PORT", 8080))

    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    print(f"🌐 PORT OPENED: {port}")


# ================= MAIN =================
async def main():
    # 1. СНАЧАЛА ОТКРЫВАЕМ ПОРТ (ВАЖНО ДЛЯ RENDER)
    await start_web()

    # 2. ПОТОМ TELEGRAM
    await client.start()
    print("🚀 TELEGRAM STARTED")

    # 3. ДЕРЖИМ ПРОЦЕСС ЖИВЫМ
    await client.run_until_disconnected()


if __name__ == "__main__":
    loop.run_until_complete(main())
