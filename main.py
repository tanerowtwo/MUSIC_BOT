import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from aiohttp import web

# === LOOP ===
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# === ENV ===
api_id = int(os.environ.get("API_ID", "0"))
api_hash = os.environ.get("API_HASH", "")
string_session = os.environ.get("STRING_SESSION", "")
target_channel = os.environ.get("TARGET_CHANNEL", "")

source_chats = [
    x.strip()
    for x in os.environ.get("SOURCE_CHATS", "").split(",")
    if x.strip()
]

# === CHECK ===
if not api_id or not api_hash or not string_session or not target_channel:
    print("❌ Missing ENV variables")
    exit(1)

# === CLIENT ===
client = TelegramClient(
    StringSession(string_session),
    api_id,
    api_hash,
    loop=loop
)

# === CHECK LINK ===
def has_link(event):
    text = (event.message.message or "").lower()

    if "youtube.com" in text or "youtu.be" in text or "music.yandex.ru" in text:
        return True

    if event.message.entities:
        for e in event.message.entities:
            if hasattr(e, "url") and e.url:
                url = e.url.lower()
                if "youtube.com" in url or "youtu.be" in url or "music.yandex.ru" in url:
                    return True

    return False


# === HANDLER ===
@client.on(events.NewMessage)
async def handler(event):
    try:
        chat_id = str(event.chat_id)

        # DEBUG (очень важно)
        print("📩 MESSAGE FROM:", chat_id)

        # FILTER
        if chat_id not in source_chats:
            return

        if not has_link(event):
            return

        # SEND FULL MESSAGE
        if event.message.media:
            await client.send_file(
                target_channel,
                file=event.message.media,
                caption=event.message.message or ""
            )
        else:
            await client.send_message(
                target_channel,
                event.message.message or ""
            )

        print("✅ SENT")

    except Exception as e:
        print("⚠️ ERROR:", e)


# === WEB SERVER ===
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
    print("🌐 WEB OK")


# === HEARTBEAT ===
async def heartbeat():
    while True:
        try:
            me = await client.get_me()
            print("💓 OK:", me.username or me.id)
        except Exception as e:
            print("💔 ERROR:", e)

        await asyncio.sleep(120)


# === MAIN ===
async def main():
    await client.start()
    print("🚀 BOT STARTED")

    await web_server()
    asyncio.create_task(heartbeat())

    await client.run_until_disconnected()


if __name__ == "__main__":
    loop.run_until_complete(main())
