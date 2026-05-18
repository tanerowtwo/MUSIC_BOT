import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ================= LOOP =================
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# ================= ENV =================
api_id = int(os.environ["API_ID"])
api_hash = os.environ["API_HASH"]
string_session = os.environ["STRING_SESSION"]

TARGET = os.environ["TARGET_CHANNEL"]

client = TelegramClient(
    StringSession(string_session),
    api_id,
    api_hash,
    loop=loop
)

# ================= LINK CHECK =================
def has_target_link(text: str) -> bool:
    if not text:
        return False

    text = text.lower()

    return (
        "youtube.com" in text
        or "youtu.be" in text
        or "music.yandex.ru" in text
    )


# ================= HANDLER =================
@client.on(events.NewMessage)
async def handler(event):
    try:
        chat = await event.get_chat()

        print("📩 MESSAGE FROM:", event.chat_id)
        print("TEXT:", event.message.message)

        text = event.message.message or ""

        # фильтр ссылок
        if not has_target_link(text):
            return

        # отправка (с медиа или без)
        if event.message.media:
            await client.send_file(
                TARGET,
                event.message.media,
                caption=text
            )
        else:
            await client.send_message(
                TARGET,
                text
            )

        print("✅ SENT")

    except Exception as e:
        print("⚠️ ERROR:", e)


# ================= START =================
async def main():
    await client.start()
    print("🚀 BOT STARTED (LISTENING ALL CHATS)")

    await client.run_until_disconnected()


if __name__ == "__main__":
    loop.run_until_complete(main())
