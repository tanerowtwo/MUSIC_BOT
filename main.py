import os
import asyncio
import re
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from aiohttp import web

# === FIX event loop (если нужно для старых окружений) ===
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

# === LINK EXTRACTION ===
def extract_links(event):
    links = set()

    text = event.message.message or ""

    # ссылки из текста
    urls = re.findall(r"https?://\S+", text)
    for url in urls:
        if (
            "music.yandex.ru" in url
            or "youtube.com" in url
            or "youtu.be" in url
        ):
            links.add(url)

    # скрытые ссылки (entities)
    if event.message.entities:
        for entity in event.message.entities:
            if hasattr(entity, "url") and entity.url:
                url = entity.url
                if (
                    "music.yandex.ru" in url
                    or "youtube.com" in url
                    or "youtu.be" in url
                ):
                    links.add(url)

    return list(links)


# === HANDLER ===
@client.on(events.NewMessage(chats=source_chats))
async def handler(event):
    try:
        links = extract_links(event)

        if not links:
            return

        chat = await event.get_chat()
        chat_name = getattr(chat, "title", None) or getattr(chat, "username", None) or "Источник"

        text = f"🎵 Из канала: {chat_name}\n\n"

        for link in links:
            if "youtube.com" in link or "youtu.be" in link:
                text += f"📺 YouTube: {link}\n"
            elif "music.yandex.ru" in link:
                text += f"🎧 Яндекс Музыка: {link}\n"
            else:
                text += f"🔗 {link}\n"

        await client.send_message(target_channel, text)

        print(f"✅ Отправлено из {chat_name}")

    except Exception as e:
        print(f"⚠️ Ошибка: {e}")


# === HTTP SERVER (Render / Railway keep-alive) ===
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


if __name__ == "__main__":
    loop.run_until_complete(main())
