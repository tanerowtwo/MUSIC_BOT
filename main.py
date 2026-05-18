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

client = TelegramClient(StringSession(string_session), api_id, api_hash, loop=loop)

# --- TELEGRAM ---
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

    if (
        "youtube.com" not in text
        and "youtu.be" not in text
        and "music.yandex.ru" not in text
    ):
        return

    if event.message.media:
        await client.send_file(TARGET, event.message.media, caption=text)
    else:
        await client.send_message(TARGET, text)

    print("✅ SENT")


# --- WEB SERVER (ВАЖНО ДЛЯ RENDER) ---
async def handle(request):
    return web.Response(text="OK")


async def web():
    app = web.Application()
    app.router.add_get("/", handle)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.environ.get("PORT", 8080))

    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    print("🌐 SERVER STARTED ON PORT", port)


# --- MAIN ---
async def main():
    await client.start()
    print("🚀 TELEGRAM STARTED")

    await web()

    await client.run_until_disconnected()


if __name__ == "__main__":
    loop.run_until_complete(main())
