import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from aiohttp import web

# === FIX для Python 3.14 ===
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# === ENV ===
api_id = int(os.environ.get("API_ID", "0"))
api_hash = os.environ.get("API_HASH", "")
string_session = os.environ.get("STRING_SESSION", "")
target_channel = os.environ.get("TARGET_CHANNEL")
source_chats = os.environ.get("SOURCE_CHATS", "").split(",")

if not api_id or not api_hash or not string_session or not target_channel:
    print("❌ Missing ENV variables")
    exit(1)

client = TelegramClient(
    StringSession(string_session),
    api_id,
    api_hash,
    loop=loop
)

# === ФУНКЦИЯ ИЗВЛЕЧЕНИЯ ССЫЛОК ===
def extract_yandex_links(event):
    links = []

    # обычные ссылки
    if event.message.message:
        text = event.message.message.lower()
        if "music.yandex.ru" in text:
            links.append(event.message.message)

    # скрытые ссылки (гиперссылки)
    if event.message.entities:
        for entity in event.message.entities:
            if hasattr(entity, "url") and entity.url:
                if "music.yandex.ru" in entity.url:
                    links.append(entity.url)

    return links


# === ОБРАБОТЧИК ===
@client.on(events.NewMessage(chats=source_chats))
async def handler(event):
    try:
        links = extract_yandex_links(event)

        if not links:
            return

        chat = await event.get_chat()
        chat_name = getattr(chat, "title", None) or getattr(chat, "username", None) or "Источник"

        text = f"🎧 Из канала: {chat_name}\n\n"

        for link in links:
            text += f"{link}\n"

        await client.send_message(target_channel, text)

        print(f"✅ Отправлено из {chat_name}")

    except Exception as e:
        print(f"⚠️ Ошибка: {e}")


# === HTTP сервер (обязательно для Render) ===
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


# === Heartbeat ===
async def heartbeat():
    while True:
        try:
            me = await client.get_me()
            print(f"💓 OK — {me.username}")
        except Exception as e:
            print(f"💔 Heartbeat error: {e}")
        await asyncio.sleep(120)


# === MAIN ===
async def main():
    await client.start()
    print("🎧 Бот Яндекс Музыки запущен")

    await web_server()
    asyncio.create_task(heartbeat())

    await client.run_until_disconnected()


if __name__ == "__main__":
    loop.run_until_complete(main())
