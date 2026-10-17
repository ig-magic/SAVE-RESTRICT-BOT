from pyrogram import Client, filters, enums
from pyrogram.types import Message
from database.db import db
from cantarella.i18n import tr


@Client.on_message(filters.private & filters.command("lang"))
async def set_lang(client: Client, message: Message):
    user_id = message.from_user.id
    if not await db.is_user_exist(user_id):
        await db.add_user(user_id, message.from_user.first_name)
    if len(message.command) < 2:
        return await message.reply_text(await tr(user_id, "lang_pick"), parse_mode=enums.ParseMode.HTML)
    lang = message.command[1].lower()
    if lang not in ("en", "hi"):
        return await message.reply_text(await tr(user_id, "lang_pick"), parse_mode=enums.ParseMode.HTML)
    await db.set_lang(user_id, lang)
    await message.reply_text(await tr(user_id, "lang_set"), parse_mode=enums.ParseMode.HTML)


@Client.on_message(filters.private & filters.command("copymode"))
async def set_copy_mode(client: Client, message: Message):
    user_id = message.from_user.id
    if not await db.is_user_exist(user_id):
        await db.add_user(user_id, message.from_user.first_name)
    if len(message.command) < 2 or message.command[1].lower() not in ("dump", "both", "pm"):
        return await message.reply_text(await tr(user_id, "copy_usage"), parse_mode=enums.ParseMode.HTML)
    mode = message.command[1].lower()
    await db.set_copy_mode(user_id, mode)
    await message.reply_text(await tr(user_id, "copy_set", mode=mode), parse_mode=enums.ParseMode.HTML)


@Client.on_message(filters.private & filters.command(["setname", "delname"]))
async def set_name(client: Client, message: Message):
    user_id = message.from_user.id
    if not await db.is_user_exist(user_id):
        await db.add_user(user_id, message.from_user.first_name)
    if message.command[0].lower() == "delname" or (
        len(message.command) >= 2 and message.command[1].lower() == "clear"
    ):
        await db.set_rename(user_id, None)
        return await message.reply_text(await tr(user_id, "name_cleared"), parse_mode=enums.ParseMode.HTML)
    if len(message.command) < 2:
        current = await db.get_rename(user_id)
        extra = f"\n\nCurrent: <code>{current}</code>" if current else ""
        return await message.reply_text(
            (await tr(user_id, "name_usage")) + extra,
            parse_mode=enums.ParseMode.HTML,
        )
    template = message.text.split(None, 1)[1].strip()
    await db.set_rename(user_id, template)
    await message.reply_text(
        await tr(user_id, "name_set", template=template),
        parse_mode=enums.ParseMode.HTML,
    )
