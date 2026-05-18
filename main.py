import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

api_id = int(os.environ["API_ID"])
api_hash = os.environ["API_HASH"]
string_session = os.environ["STRING_SESSION"]

client = TelegramClient(StringSession(string_session), api_id, api_hash, loop=loop)

# --- НОРМАЛИЗАЦИЯ ЧАТОВ ---
SOURCE_CHATS = set(
    x.strip().lstrip("@")
    for x in os.environ.get("SOURCE_CHATS", "").split(",")
    if x.strip()
)

TARGET = os.environ["TARGET_CHANNEL"]


def is_target_link(text):
    text = (text or "").lower()
    return (
        "youtube.com" in text
        or "youtu.be" in text
        or "music.yandex.ru" in text
    )


@client.on(events.NewMessage)
async def handler(event):
    try:
        chat = await event.get_chat()

        username = getattr(chat, "username", None)
        chat_id = str(event.chat_id)

        # --- DEBUG (ОБЯЗАТЕЛЬНО) ---
        print("CHAT:", chat_id, username)

        # --- FILTER (БЕЗ ЛОМАНЫХ УСЛОВИЙ) ---
        if username:
            username = username.lstrip("@")
            if username not in SOURCE_CHATS and chat_id not in SOURCE_CHATS:
                return
        else:
            if chat_id not in SOURCE_CHATS:
                return

        # --- CHECK LINK ---
        text = event.message.message or ""
        if not is_target_link(text):
            return

        # --- SEND ---
        if event.message.media:
            await client.send_file(
                TARGET,
                event.message.media,
                caption=text
            )
        else:
            await client.send_message(TARGET, text)

        print("✅ SENT")

    except Exception as e:
        print("⚠️ ERROR:", e)


async def main():
    await client.start()
    print("🚀 BOT RUNNING")
    await client.run_until_disconnected()


if __name__ == "__main__":
    loop.run_until_complete(main())
