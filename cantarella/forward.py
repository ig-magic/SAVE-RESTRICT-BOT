import asyncio
import os
import shutil
import time
from html import escape

from pyrogram import Client, filters, StopPropagation, enums
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery

from config import API_ID, API_HASH
from database.db import db
from cantarella.i18n import tr
from cantarella.textutil import clean_text, rename_path
from cantarella.fsub import ensure_fsub
from logger import LOGGER

logger = LOGGER(__name__)
MAX_FORWARD = 3000

JOBS = {}
RUNNING = set()


def in_forward_setup(user_id):
    job = JOBS.get(user_id)
    return bool(job) and job.get("step") in ("target", "source", "skip", "confirm")


def forward_is_running(user_id):
    return user_id in RUNNING


def cancel_forward(user_id):
    job = JOBS.get(user_id)
    if job:
        job["cancel"] = True
    RUNNING.discard(user_id)
    JOBS.pop(user_id, None)


def parse_source_link(text):
    raw = (text or "").strip().split()[0].split("?")[0]
    lowered = raw.replace("https://", "").replace("http://", "")
    if lowered.startswith("telegram.me/"):
        lowered = "t.me/" + lowered[len("telegram.me/"):]
    if "t.me/" not in lowered:
        return None
    parts = [p for p in lowered.split("/") if p and p != "t.me"]
    if parts and parts[0] == "s":
        parts = parts[1:]
    if len(parts) < 2:
        return None
    private = False
    if parts[0] == "c" and len(parts) >= 3:
        private = True
        source = int("-100" + parts[1])
        tail = parts[2]
    elif parts[0] == "b" and len(parts) >= 3:
        source = parts[1]
        tail = parts[2]
    else:
        source = parts[0]
        tail = parts[1]
    tail = tail.replace("?single", "")
    if "-" in tail:
        left, right = tail.split("-", 1)
        start, end = int(left), int(right)
        mode = "range"
    else:
        end = int(tail)
        start = 1
        mode = "all"
    if start < 1 or end < start:
        return None
    return {"source": source, "start": start, "end": end, "mode": mode, "private": private}


def status_text(stats, owner, state):
    total = stats["total"] or 1
    percent = min(100, int(stats["done"] * 100 / total))
    head = "ᴄᴏᴍᴘʟᴇᴛᴇᴅ" if state == "completed" else "ғᴏʀᴡᴀʀᴅ sᴛᴀᴛᴜs"
    foot = "ᴄᴏᴍᴘʟᴇᴛᴇᴅ" if state == "completed" else ("ᴄᴀɴᴄᴇʟʟᴇᴅ" if state == "cancelled" else "ᴘᴇɴᴅɪɴɢ")
    label = "completed" if state == "completed" else ("cancelled" if state == "cancelled" else "pending")
    return (
        f"╔════❰ {head}  ❱═❍⊱❁۪۪\n"
        f"║╭━━━━━━━━━━━━━━━➣\n"
        f"║┣⪼🕵 ғᴇᴛᴄʜᴇᴅ Msɢ : {stats['fetched']}\n"
        f"║┃\n"
        f"║┣⪼✅ sᴜᴄᴄᴇғᴜʟʟʏ Fᴡᴅ : {stats['success']}\n"
        f"║┃\n"
        f"║┣⪼👥 ᴅᴜᴘʟɪᴄᴀᴛᴇ Msɢ : {stats['duplicate']}\n"
        f"║┃\n"
        f"║┣⪼🗑 ᴅᴇʟᴇᴛᴇᴅ Msɢ : {stats['deleted']}\n"
        f"║┃\n"
        f"║┣⪼🪆 Sᴋɪᴘᴘᴇᴅ Msɢ : {stats['skipped']}\n"
        f"║┃\n"
        f"║┣⪼🔁 Fɪʟᴛᴇʀᴇᴅ Msɢ : {stats['filtered']}\n"
        f"║┃\n"
        f"║┣⪼📊 Cᴜʀʀᴇɴᴛ Sᴛᴀᴛᴜs: {label}\n"
        f"║┃\n"
        f"║┣⪼𖨠 Pᴇʀᴄᴇɴᴛᴀɢᴇ: {percent}%\n"
        f"║┃\n"
        f"║┣⪼🙍🏻 {escape(owner)}📛\n"
        f"║╰━━━━━━━━━━━━━━━➣\n"
        f"╚════❰ {foot} ❱══❍⊱❁۪۪"
    )


async def _chat_label(client, chat_id):
    try:
        chat = await client.get_chat(chat_id)
        return chat.title or getattr(chat, "first_name", None) or str(chat_id)
    except Exception:
        return str(chat_id)


async def _can_post(client, chat_id):
    try:
        member = await client.get_chat_member(chat_id, "me")
    except Exception:
        return False
    status = member.status
    if status == enums.ChatMemberStatus.OWNER:
        return True
    if status == enums.ChatMemberStatus.ADMINISTRATOR:
        priv = getattr(member, "privileges", None)
        if priv is None:
            return True
        return bool(getattr(priv, "can_post_messages", False) or getattr(priv, "can_send_messages", False))
    if status == enums.ChatMemberStatus.MEMBER:
        try:
            chat = await client.get_chat(chat_id)
        except Exception:
            return False
        return chat.type in (enums.ChatType.GROUP, enums.ChatType.SUPERGROUP)
    return False


async def _open_user(user_id):
    session = await db.get_session(user_id)
    if not session:
        return None
    acc = Client(
        f"fwd{user_id}",
        session_string=session,
        api_id=API_ID,
        api_hash=API_HASH,
        in_memory=True,
    )
    await acc.connect()
    return acc


def _is_deleted(exc):
    text = str(exc).upper()
    return any(token in text for token in ("MESSAGE_ID_INVALID", "MESSAGE_DELETED", "MSG_ID_INVALID", "CHANNEL_INVALID"))


async def _send_downloaded(bot, acc, msg, target, user_id, index):
    if msg.text and not (msg.photo or msg.video or msg.document or msg.audio or msg.voice or msg.animation or msg.sticker):
        text = await clean_text(user_id, msg.text)
        if not text:
            return "filtered"
        await bot.send_message(target, text)
        return "ok"
    temp = f"downloads/fwd_{user_id}_{msg.id}"
    os.makedirs(temp, exist_ok=True)
    try:
        path = await acc.download_media(msg, file_name=f"{temp}/")
        if not path:
            return "filtered"
        path = await rename_path(user_id, path, index=index)
        caption = await clean_text(user_id, msg.caption or "") or None
        if msg.photo:
            await bot.send_photo(target, path, caption=caption)
        elif msg.video:
            await bot.send_video(target, path, caption=caption, duration=msg.video.duration, width=msg.video.width, height=msg.video.height)
        elif msg.audio:
            await bot.send_audio(target, path, caption=caption)
        elif msg.voice:
            await bot.send_voice(target, path)
        elif msg.animation:
            await bot.send_animation(target, path, caption=caption)
        elif msg.sticker:
            await bot.send_sticker(target, path)
        elif msg.document:
            await bot.send_document(target, path, caption=caption)
        else:
            return "filtered"
        return "ok"
    finally:
        shutil.rmtree(temp, ignore_errors=True)


async def _relay(bot, acc, source, msgid, target, user_id, index):
    try:
        await bot.copy_message(target, source, msgid)
        return "ok"
    except FloodWait as exc:
        await asyncio.sleep(int(exc.value) + 1)
        try:
            await bot.copy_message(target, source, msgid)
            return "ok"
        except Exception as exc:
            err = exc
    except Exception as exc:
        err = exc
    if _is_deleted(err):
        return "deleted"
    if acc is None:
        return "filtered"
    try:
        msg = await acc.get_messages(source, msgid)
    except Exception:
        return "filtered"
    if not msg or getattr(msg, "empty", False):
        return "deleted"
    try:
        return await _send_downloaded(bot, acc, msg, target, user_id, index)
    except FloodWait as exc:
        await asyncio.sleep(int(exc.value) + 1)
        try:
            return await _send_downloaded(bot, acc, msg, target, user_id, index)
        except Exception as exc:
            logger.error(f"Forward send failed {source}/{msgid}: {exc}")
            return "filtered"
    except Exception as exc:
        logger.error(f"Forward send failed {source}/{msgid}: {exc}")
        return "filtered"


async def _edit_status(status_msg, stats, owner, state):
    try:
        await status_msg.edit_text(status_text(stats, owner, state), parse_mode=enums.ParseMode.HTML)
    except FloodWait as exc:
        await asyncio.sleep(int(exc.value) + 1)
    except Exception:
        pass


async def run_forward(bot, user_id, job, status_msg):
    source = job["source"]
    target = job["target"]
    skip = job["skip"]
    owner = job["owner"]
    start = source["start"] + skip
    end = source["end"]
    stats = {
        "fetched": 0,
        "success": 0,
        "duplicate": 0,
        "deleted": 0,
        "skipped": skip,
        "filtered": 0,
        "done": 0,
        "total": max(0, end - start + 1),
    }
    acc = None
    last_edit = 0
    try:
        try:
            acc = await _open_user(user_id)
        except Exception as exc:
            logger.error(f"User session connect failed: {exc}")
            acc = None
        for msgid in range(start, end + 1):
            if job.get("cancel") or user_id not in RUNNING:
                await _edit_status(status_msg, stats, owner, "cancelled")
                return
            stats["fetched"] += 1
            stats["done"] += 1
            if await db.has_forwarded(user_id, source["source"], msgid):
                stats["duplicate"] += 1
            else:
                result = await _relay(bot, acc, source["source"], msgid, target, user_id, stats["success"] + 1)
                if result == "ok":
                    stats["success"] += 1
                    await db.mark_forwarded(user_id, source["source"], msgid)
                elif result == "deleted":
                    stats["deleted"] += 1
                else:
                    stats["filtered"] += 1
            now = time.time()
            if stats["done"] == stats["total"] or stats["done"] % 5 == 0 or now - last_edit > 4:
                await _edit_status(status_msg, stats, owner, "pending")
                last_edit = now
            await asyncio.sleep(0.4)
        await _edit_status(status_msg, stats, owner, "completed")
    except Exception as exc:
        logger.error(f"Forward job failed: {exc}")
        try:
            await status_msg.reply_text(f"❌ Forward stopped.\n<code>{escape(str(exc))}</code>", parse_mode=enums.ParseMode.HTML)
        except Exception:
            pass
    finally:
        RUNNING.discard(user_id)
        JOBS.pop(user_id, None)
        if acc:
            try:
                await acc.disconnect()
            except Exception:
                pass


async def _can_read(client, source):
    try:
        await client.get_chat(source)
        return True
    except Exception:
        return False


async def _show_confirm(client, user_id, job, message):
    source = job["source"]
    target_title = await _chat_label(client, job["target"])
    source_title = await _chat_label(client, source["source"])
    me = await client.get_me()
    problems = []
    if not await _can_post(client, job["target"]):
        problems.append("• Bot is not admin in the target chat, or cannot post.")
    source_ok = await _can_read(client, source["source"])
    session = await db.get_session(user_id)
    if source["private"] and not source_ok and not session:
        problems.append("• Private source: /login first, or add this bot as admin there.")
    if not source["private"] and not source_ok and not session:
        problems.append("• Bot cannot see the source chat. Add it there, or /login.")
    count = source["end"] - (source["start"] + job["skip"]) + 1
    text = await tr(
        user_id, "fwd_check",
        bot=escape(me.first_name or me.username or "bot"),
        source=escape(source_title),
        target=escape(target_title),
        skip=job["skip"],
        start=source["start"] + job["skip"],
        end=source["end"],
        count=count,
    )
    buttons = []
    if problems:
        text += await tr(user_id, "fwd_check_fail", problems="\n".join(problems))
    else:
        buttons.append([
            InlineKeyboardButton(await tr(user_id, "fwd_yes"), callback_data="fwd:yes"),
            InlineKeyboardButton(await tr(user_id, "fwd_no"), callback_data="fwd:no"),
        ])
    if problems:
        buttons.append([InlineKeyboardButton(await tr(user_id, "fwd_no"), callback_data="fwd:no")])
    job["step"] = "confirm"
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=enums.ParseMode.HTML)


async def _ask_source(client, user_id, message):
    JOBS[user_id]["step"] = "source"
    await message.reply_text(await tr(user_id, "fwd_source"), parse_mode=enums.ParseMode.HTML)


@Client.on_message(filters.private & filters.command("forward"))
async def forward_start(client: Client, message: Message):
    user = message.from_user
    if not user:
        return
    if not await db.is_user_exist(user.id):
        await db.add_user(user.id, user.first_name)
    if not await ensure_fsub(client, message):
        return
    if user.id in RUNNING:
        return await message.reply_text(await tr(user.id, "fwd_busy"))
    if in_forward_setup(user.id):
        return await message.reply_text(await tr(user.id, "fwd_setup_busy"))
    chats = await db.list_dump_chats(user.id)
    if not chats:
        return await message.reply_text(await tr(user.id, "fwd_need_dump"), parse_mode=enums.ParseMode.HTML)
    JOBS[user.id] = {
        "step": "target",
        "target": None,
        "source": None,
        "skip": 0,
        "cancel": False,
        "owner": user.first_name or user.username or str(user.id),
    }
    if len(chats) == 1:
        JOBS[user.id]["target"] = chats[0]
        return await _ask_source(client, user.id, message)
    buttons = []
    for chat_id in chats:
        title = await _chat_label(client, chat_id)
        buttons.append([InlineKeyboardButton(title[:40], callback_data=f"fwd:t:{chat_id}")])
    await message.reply_text(
        await tr(user.id, "fwd_choose"),
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=enums.ParseMode.HTML,
    )


@Client.on_message(filters.private & filters.text & ~filters.command(["cancel", "forward"]), group=-1)
async def forward_text(client: Client, message: Message):
    user = message.from_user
    if not user or not in_forward_setup(user.id):
        return
    job = JOBS[user.id]
    step = job["step"]
    if step == "source":
        parsed = None
        try:
            parsed = parse_source_link(message.text)
        except Exception:
            parsed = None
        if not parsed:
            await message.reply_text(await tr(user.id, "fwd_bad_link"))
            raise StopPropagation
        count = parsed["end"] - parsed["start"] + 1
        if count > MAX_FORWARD:
            await message.reply_text(
                await tr(user.id, "fwd_range_big", count=count, max=MAX_FORWARD),
                parse_mode=enums.ParseMode.HTML,
            )
            raise StopPropagation
        job["source"] = parsed
        job["step"] = "skip"
        await message.reply_text(await tr(user.id, "fwd_skip"), parse_mode=enums.ParseMode.HTML)
        raise StopPropagation
    if step == "skip":
        raw = message.text.strip()
        if not raw.isdigit():
            await message.reply_text(await tr(user.id, "fwd_bad_skip"))
            raise StopPropagation
        skip = int(raw)
        selected = job["source"]["end"] - job["source"]["start"] + 1
        if skip >= selected:
            await message.reply_text(await tr(user.id, "fwd_skip_big"))
            raise StopPropagation
        job["skip"] = skip
        await _show_confirm(client, user.id, job, message)
        raise StopPropagation
    if step == "confirm":
        await message.reply_text("Use the Yes button, or /cancel.")
        raise StopPropagation


@Client.on_callback_query(filters.regex(r"^fwd:"), group=-1)
async def forward_buttons(client: Client, query: CallbackQuery):
    user = query.from_user
    if not user:
        return
    job = JOBS.get(user.id)
    data = query.data
    if data == "fwd:no":
        cancel_forward(user.id)
        await query.answer()
        await query.message.reply_text(await tr(user.id, "fwd_cancelled"))
        raise StopPropagation
    if not job:
        await query.answer("Start again with /forward", show_alert=True)
        raise StopPropagation
    if data.startswith("fwd:t:"):
        job["target"] = int(data.split(":", 2)[2])
        await query.answer()
        await _ask_source(client, user.id, query.message)
        raise StopPropagation
    if data == "fwd:yes" and job.get("step") == "confirm":
        if user.id in RUNNING:
            await query.answer("Already running", show_alert=True)
            raise StopPropagation
        RUNNING.add(user.id)
        job["step"] = "running"
        await query.answer(await tr(user.id, "fwd_started"))
        status = await query.message.reply_text(
            status_text(
                {"fetched": 0, "success": 0, "duplicate": 0, "deleted": 0, "skipped": job["skip"], "filtered": 0, "done": 0, "total": 1},
                job["owner"],
                "pending",
            ),
            parse_mode=enums.ParseMode.HTML,
        )
        asyncio.create_task(run_forward(client, user.id, job, status))
        raise StopPropagation
    await query.answer()
    raise StopPropagation


@Client.on_message(filters.private & filters.command("cancel"), group=2)
async def cancel_forward_cmd(client: Client, message: Message):
    user = message.from_user
    if not user:
        return
    if user.id in RUNNING or in_forward_setup(user.id):
        cancel_forward(user.id)
        await message.reply_text(await tr(user.id, "fwd_cancelled"))
        raise StopPropagation
