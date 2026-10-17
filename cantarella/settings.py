import os
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.db import db
from cantarella.strings import COMMANDS_TXT
# ======================================================
# /settings - Enhanced Professional Settings Menu
# ======================================================
@Client.on_message(filters.command("settings") & filters.private)
async def settings_menu(client: Client, message: Message):
    user_id = message.from_user.id
    # Ensure user exists (Safe Call)
    if not await db.is_user_exist(user_id):
        await db.add_user(user_id, message.from_user.first_name)
    # Fetch real status
    is_premium = await db.check_premium(user_id)
    premium_badge = "💎 Premium Member" if is_premium else "👤 Free User"
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📜 Commands List", callback_data="cmd_list_btn")],
        [InlineKeyboardButton("📊 My Usage Stats", callback_data="user_stats_btn")],
        [InlineKeyboardButton("🗑 Dump Chat", callback_data="dump_chat_btn")],
        [
            InlineKeyboardButton("🖼 Thumbnail", callback_data="thumb_btn"),
            InlineKeyboardButton("📝 Caption", callback_data="caption_btn")
        ],
        [InlineKeyboardButton("❌ Close Menu", callback_data="close_btn")]
    ])
    text = (
        f"<b>⚙️ Settings Panel</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"<b>Account:</b> {premium_badge}\n"
        f"<b>User ID:</b> <code>{user_id}</code>\n\n"
        f"<i>Select an option below to customize your experience.</i>"
    )
    await message.reply_text(text, reply_markup=buttons, parse_mode=enums.ParseMode.HTML)
# ======================================================
# /commands - Direct Access to Commands List
# ======================================================
@Client.on_message(filters.command("commands") & filters.private)
async def direct_commands(client: Client, message: Message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙️ Open Settings", callback_data="settings_back_btn"), InlineKeyboardButton("❌ Close", callback_data="close_btn")]
    ])
    await message.reply_text(
        COMMANDS_TXT,
        reply_markup=buttons,
        parse_mode=enums.ParseMode.HTML,
        disable_web_page_preview=True
    )
# ======================================================
# /setchat - Set or Clear Dump Chat
# ======================================================
@Client.on_message(filters.command("setchat") & filters.private)
async def set_dump_chat(client: Client, message: Message):
    user_id = message.from_user.id
    if not await db.is_user_exist(user_id):
        await db.add_user(user_id, message.from_user.first_name)
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>🗑 Set Dump Chat</b>\n\n"
            "<b>Usage:</b>\n"
            "<code>/setchat &lt;chat_id&gt;</code> → Add a dump chat\n"
            "<code>/setchat @channel</code> → Add by username\n"
            "<code>/setchat list</code> → Show all dump chats\n"
            "<code>/setchat remove &lt;chat_id&gt;</code> → Remove one\n"
            "<code>/setchat clear</code> → Remove all\n\n"
            "<i>Add this bot as admin, with Post Messages. Add 2 or more, then /forward can choose a target.</i>\n"
            "<i>Example: /setchat -1001234567890</i>",
            parse_mode=enums.ParseMode.HTML
        )
    arg_raw = message.command[1].strip()
    if arg_raw.lower() == "clear":
        await db.clear_dump_chats(user_id)
        return await message.reply_text(
            "✅ <b>All dump chats cleared</b>\n\n<i>New saved posts will come to this chat again.</i>",
            parse_mode=enums.ParseMode.HTML
        )
    if arg_raw.lower() == "list":
        chats = await db.list_dump_chats(user_id)
        if not chats:
            return await message.reply_text("🗑 No dump chats set.")
        lines = []
        for chat_id in chats:
            try:
                chat = await client.get_chat(chat_id)
                title = chat.title or "Private Chat"
            except Exception:
                title = "Unknown"
            lines.append(f"• {title} — <code>{chat_id}</code>")
        return await message.reply_text(
            "<b>🗑 Dump chats</b>\n" + "\n".join(lines),
            parse_mode=enums.ParseMode.HTML
        )
    if arg_raw.lower() == "remove":
        if len(message.command) < 3 or not message.command[2].lstrip("-").isdigit():
            return await message.reply_text("❌ <code>/setchat remove -100...</code>", parse_mode=enums.ParseMode.HTML)
        left = await db.remove_dump_chat(user_id, int(message.command[2]))
        return await message.reply_text(f"✅ Removed. {len(left)} dump chat(s) left.")
    try:
        if arg_raw.lstrip("-").isdigit():
            chat = await client.get_chat(int(arg_raw))
        else:
            chat = await client.get_chat(arg_raw)
        chat_id = chat.id
        chat_title = chat.title or getattr(chat, "first_name", None) or "Private Chat"
        await client.send_message(
            chat_id,
            "✅ Dump chat connected. Saved posts will be posted here."
        )
        chats = await db.add_dump_chat(user_id, chat_id)
        await message.reply_text(
            f"✅ <b>Dump chat added</b>\n\n"
            f"<b>Chat:</b> {chat_title}\n"
            f"<b>Chat ID:</b> <code>{chat_id}</code>\n"
            f"<b>Total dump chats:</b> {len(chats)}\n\n"
            f"<i>A test message was sent there. Add 2 or more, then use /forward to pick a target.</i>",
            parse_mode=enums.ParseMode.HTML
        )
    except Exception as e:
        await message.reply_text(
            "❌ <b>Bot cannot post in that chat</b>\n\n"
            "1. Add this bot to the channel or group\n"
            "2. Make it <b>admin</b>\n"
            "3. Turn on <b>Post Messages</b>\n"
            "4. Run <code>/setchat</code> again\n\n"
            f"<code>{e}</code>",
            parse_mode=enums.ParseMode.HTML
        )
# ======================================================
# Callbacks - Full Settings Navigation
# ======================================================
@Client.on_callback_query(filters.regex("^(cmd_list_btn|dump_chat_btn|thumb_btn|caption_btn|user_stats_btn|settings_back_btn|close_btn)$"))
async def settings_callbacks(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id
   
    # Common back/close buttons
    back_close = [[InlineKeyboardButton("⬅️ Back", callback_data="settings_back_btn"), InlineKeyboardButton("❌ Close", callback_data="close_btn")]]
    if data == "cmd_list_btn":
        await callback_query.edit_message_text(
            COMMANDS_TXT,
            reply_markup=InlineKeyboardMarkup(back_close),
            parse_mode=enums.ParseMode.HTML,
            disable_web_page_preview=True
        )
    elif data == "dump_chat_btn":
        current = await db.list_dump_chats(user_id)
        if current:
            lines = []
            for chat_id in current:
                try:
                    chat = await client.get_chat(chat_id)
                    title = chat.title or "Private Chat"
                except Exception:
                    title = "Unknown"
                lines.append(f"• {title} — <code>{chat_id}</code>")
            text = (
                f"<b>🗑 Dump chats ({len(current)})</b>\n\n"
                + "\n".join(lines)
                + "\n\n<i>Saved posts go here. /forward picks one target when you have 2 or more.</i>"
            )
        else:
            text = (
                "<b>🗑 No Dump Chat Set</b>\n\n"
                "<i>Saved files appear only in this chat.</i>\n"
                "<i>Use /setchat &lt;chat_id&gt; to enable forwarding.</i>"
            )
        await callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(back_close), parse_mode=enums.ParseMode.HTML)
    elif data == "thumb_btn":
        thumb = await db.get_thumbnail(user_id)
        if thumb and os.path.exists(thumb):
            await callback_query.message.reply_photo(
                thumb,
                caption="<b>🖼 Your Current Custom Thumbnail</b>\n\n<i>Send a new photo to update • /del_thumb to remove</i>",
                parse_mode=enums.ParseMode.HTML
            )
            await callback_query.answer("Thumbnail preview sent below 👇")
        else:
            await callback_query.edit_message_text(
                "<b>🖼 No Custom Thumbnail Set</b>\n\n"
                "<i>Send a photo to set as default thumbnail for uploads.</i>",
                reply_markup=InlineKeyboardMarkup(back_close),
                parse_mode=enums.ParseMode.HTML
            )
    elif data == "caption_btn":
        caption = await db.get_caption(user_id)
        if caption:
            preview = caption.format(filename="Video_File_2024.mp4", size="1.2 GB")
            text = (
                f"<b>📝 Current Custom Caption</b>\n\n"
                f"<code>{caption}</code>\n\n"
                f"<b>Preview:</b>\n{preview}\n\n"
                "<i>Placeholders: {filename}, {size}</i>\n"
                "<i>/set_caption &lt;text&gt; to change • /del_caption to remove</i>"
            )
        else:
            text = (
                "<b>📝 No Custom Caption Set</b>\n\n"
                "<i>Use /set_caption &lt;text&gt; to set one.</i>\n"
                "<i>Supports {filename} and {size} placeholders.</i>"
            )
        await callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(back_close), parse_mode=enums.ParseMode.HTML)
    elif data == "user_stats_btn":
        # Fetch real stats from DB
        is_premium = await db.check_premium(user_id)
        user_data = await db.col.find_one({'id': int(user_id)})
       
        if is_premium:
            limit_text = "♾️ Unlimited"
            usage_text = "Ignored (Premium)"
        else:
            # Free user logic
            daily_limit = 10
            used = user_data.get('daily_usage', 0)
            limit_text = f"{daily_limit} Files / 24h"
            usage_text = f"{used} / {daily_limit}"
        text = (
            f"<b>📊 My Usage Statistics</b>\n\n"
            f"<b>Plan:</b> {'💎 Premium' if is_premium else '👤 Free'}\n"
            f"<b>Daily Limit:</b> <code>{limit_text}</code>\n"
            f"<b>Today's Usage:</b> <code>{usage_text}</code>\n\n"
            f"<i>Upgrade to Premium for unlimited downloads!</i>"
        )
        await callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(back_close), parse_mode=enums.ParseMode.HTML)
    elif data == "settings_back_btn":
        # Re-render main menu
        is_premium = await db.check_premium(user_id)
        premium_badge = "💎 Premium Member" if is_premium else "👤 Free User"
       
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("📜 Commands List", callback_data="cmd_list_btn")],
            [InlineKeyboardButton("📊 My Usage Stats", callback_data="user_stats_btn")],
            [InlineKeyboardButton("🗑 Dump Chat", callback_data="dump_chat_btn")],
            [
                InlineKeyboardButton("🖼 Thumbnail", callback_data="thumb_btn"),
                InlineKeyboardButton("📝 Caption", callback_data="caption_btn")
            ],
            [InlineKeyboardButton("❌ Close Menu", callback_data="close_btn")]
        ])
       
        text = (
            f"<b>⚙️ Settings Panel</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"<b>Account:</b> {premium_badge}\n"
            f"<b>User ID:</b> <code>{user_id}</code>\n\n"
            f"<i>Select an option below to customize your experience.</i>"
        )
       
        await callback_query.edit_message_text(text, reply_markup=buttons, parse_mode=enums.ParseMode.HTML)
    elif data == "close_btn":
        await callback_query.message.delete()
    await callback_query.answer()
