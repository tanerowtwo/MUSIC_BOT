import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from aiohttp import web

# === FIX event loop ===
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# === ENV ===
api_id = int(os.environ.get("API_ID", "0"))
api_hash = os.environ.get("API_HASH", "")
string_session = os.environ.get("STRING_SESSION", "")
target_channel = os.environ.get("TARGET_CHANNEL")

source_chats = [
    chat.strip()
    for chat in os.environ.get("SOURCE_CHATS", "").split(",")
    if chat.strip()
]

# === CHECK ENV ===
if not api_id or not api_hash or not string_session or not target_channel:
    print("❌ Missing ENV variables")
    exit(1)

# === TELEGRAM CLIENT ===
client = TelegramClient(
    StringSession(string_session),
    api_id,
    api_hash,
    loop=loop
)

# === ПРОВЕРКА СООБЩЕНИЯ НА НУЖНЫЕ ССЫЛКИ ===
def contains_target_link(event):
    text = (event.message.message or "").lower()

    # обычные ссылки
    if (
        "music.yandex.ru" in text
        or "youtube.com" in text
        or "youtu.be" in text
    ):
        return True

    # скрытые ссылки
    if event.message.entities:
        for entity in event.message.entities:
            if hasattr(entity, "url") and entity.url:
                url = entity.url.lower()

                if (
                    "music.yandex.ru" in url
                    or "youtube.com" in url
                    or "youtu.be" in url
                ):
                    return True

    return False


# === HANDLER ===
@client.on(events.NewMessage)
async def handler(event):
    try:
        chat = await event.get_chat()

        username = getattr(chat, "username", None)

        # === FILTER SOURCE CHATS ===
        allowed = False

        # проверка по ID
        if str(event.chat_id) in source_chats:
            allowed = True

        # проверка по username
        if username:
            if (
                username in source_chats
                or f"@{username}" in source_chats
            ):
                allowed = True

        if not allowed:
            return

        # === CHECK LINKS ===
        if not contains_target_link(event):
            return

        # === FORWARD ORIGINAL MESSAGE ===
        await client.forward_messages(
            target_channel,
            event.message
        )

        print(f"✅ Переслано сообщение из {event.chat_id}")

    except Exception as e:
        print(f"⚠️ Ошибка: {e}")


# === HTTP SERVER ===
async def handle(request):
    return web.Response(text="OK")

async def web_server():
    app = web.Application()

    app.router.add_get("/", handle)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        int(os.environ.get("PORT", 8080))
    )

    await site.start()

    print("🌐 Web server started")


# === HEARTBEAT ===
async def heartbeat():
    while True:
        try:
            me = await client.get_me()

            print(f"💓 OK — {me.username or me.id}")

        except Exception as e:
            print(f"💔 Heartbeat error: {e}")

        await asyncio.sleep(120)


# === MAIN ===
async def main():
    await client.start()

    print("🎧 Бот запущен")

    await web_server()

    asyncio.create_task(heartbeat())

    await client.run_until_disconnected()


# === START ===
if __name__ == "__main__":
    loop.run_until_complete(main())
