from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from config import ADMINS
from database.db import db
from cantarella.i18n import tr

JOINED = {
    ChatMemberStatus.OWNER,
    ChatMemberStatus.ADMINISTRATOR,
    ChatMemberStatus.MEMBER,
}


async def missing_channels(client: Client, user_id: int):
    missing = []
    for chat in await db.list_fsub():
        try:
            member = await client.get_chat_member(chat["id"], user_id)
            if member.status not in JOINED:
                missing.append(chat)
        except Exception:
            missing.append(chat)
    return missing


async def ensure_fsub(client: Client, message: Message) -> bool:
    """Return True when the user may continue. Admins are not blocked."""
    user = message.from_user
    if not user:
        return True
    if user.id in ADMINS:
        return True
    missing = await missing_channels(client, user.id)
    if not missing:
        return True
    buttons = []
    for chat in missing:
        link = chat.get("link")
        if link:
            buttons.append([InlineKeyboardButton(chat.get("title") or "Join", url=link)])
    await message.reply_text(
        await tr(user.id, "fsub_need"),
        reply_markup=InlineKeyboardMarkup(buttons) if buttons else None,
        parse_mode="html",
    )
    return False


async def _resolve_channel(client, raw):
    if raw.lstrip("-").isdigit():
        chat = await client.get_chat(int(raw))
    else:
        chat = await client.get_chat(raw)
    link = f"https://t.me/{chat.username}" if chat.username else getattr(chat, "invite_link", None)
    if not link:
        try:
            link = await client.export_chat_invite_link(chat.id)
        except Exception:
            link = None
    return {"id": chat.id, "title": chat.title or str(chat.id), "link": link}


@Client.on_message(filters.command(["fsub", "add_unsubscribe", "del_unsubscribe"]) & filters.user(ADMINS))
async def fsub_admin(client: Client, message: Message):
    cmd = (message.command[0] if message.command else "fsub").lower()
    args = message.command[1:]
    action = args[0].lower() if args else ""
    if cmd == "add_unsubscribe":
        action, args = "add", args
    elif cmd == "del_unsubscribe":
        action, args = "del", args
    if action in ("", "list"):
        channels = await db.list_fsub()
        if not channels:
            return await message.reply_text("No force-subscribe channels.\n`/fsub add @channel`")
        lines = "\n".join(f"• {c.get('title')} — `{c.get('id')}`" for c in channels)
        return await message.reply_text(f"**Force subscribe**\n{lines}")
    if action == "add" and len(args) >= 2:
        try:
            chat = await _resolve_channel(client, args[1])
            await db.add_fsub(chat)
            return await message.reply_text(f"Added **{chat['title']}** (`{chat['id']}`).")
        except Exception as e:
            return await message.reply_text(f"Could not add channel.\n`{e}`")
    if action == "del" and len(args) >= 2:
        raw = args[1]
        try:
            chat_id = int(raw) if raw.lstrip("-").isdigit() else (await client.get_chat(raw)).id
            await db.del_fsub(chat_id)
            return await message.reply_text(f"Removed `{chat_id}`.")
        except Exception as e:
            return await message.reply_text(f"Could not remove channel.\n`{e}`")
    await message.reply_text(
        "**Usage**\n"
        "`/fsub list`\n"
        "`/fsub add @channel`\n"
        "`/fsub del @channel`"
    )
