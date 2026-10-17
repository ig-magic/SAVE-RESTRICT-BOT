from database.db import db

STRINGS = {
    "en": {
        "queued": "⏳ Queued. Position <b>{n}</b>.\n<i>/cancel stops the current task and clears the queue.</i>",
        "queue_cleared": "✅ Queue cleared.",
        "batch_cancelled": "✅ Batch cancelled. Queue cleared.",
        "nothing_active": "❌ No active login, save, or forward.",
        "lang_set": "✅ Language set to <b>English</b>.",
        "lang_pick": "<b>Choose language</b>\n/lang en\n/lang hi",
        "copy_set": "✅ Copy mode: <b>{mode}</b>\n\n<b>dump</b> — only dump chats\n<b>both</b> — dump chats and this chat\n<b>pm</b> — only this chat",
        "copy_usage": "<b>Usage:</b> <code>/copymode dump</code>, <code>both</code>, or <code>pm</code>",
        "name_set": "✅ Rename template saved.\n<code>{template}</code>\n\nPlaceholders: <code>{filename}</code> <code>{index}</code> <code>{ext}</code>",
        "name_cleared": "✅ Rename template removed.",
        "name_usage": "<b>Usage:</b>\n<code>/setname MyFile_{index}</code>\n<code>/setname clear</code>",
        "fsub_need": "<b>Join the required channel to continue.</b>",
        "fsub_join": "Join",
        "fwd_busy": "A forward is already running. /cancel to stop it.",
        "fwd_setup_busy": "A forward setup is already open. /cancel to stop it.",
        "fwd_need_dump": "<b>No dump chat set.</b>\nAdd the bot as admin in your channel, then <code>/setchat -100...</code> or <code>/setchat @channel</code>.",
        "fwd_choose": "<b>Forward Bot ⚡️</b>\n\n<b>❪ CHOOSE TARGET CHAT ❫</b>\n\nChoose your target chat from the buttons.\n/cancel — cancel this process",
        "fwd_source": "<b>❪ SET SOURCE CHAT ❫</b>\n\nSend the <b>last message link</b> if you want every post up to that message.\nOr a range: <code>https://t.me/channel/1-100</code>\n\nPrivate: <code>https://t.me/c/123456/500</code>\n/cancel — cancel this process",
        "fwd_bad_link": "❌ Send a Telegram message link, or /cancel.",
        "fwd_range_big": "❌ That range is <b>{count}</b> messages. Max per run is <b>{max}</b>.\nSend a smaller range. Already forwarded posts are skipped, so you can continue with the next range.",
        "fwd_skip": "<b>❪ SET MESSAGE SKIP NUMBER ❫</b>\n\nSkip this many messages from the start. The rest will be forwarded.\nDefault = 0\n\n0 = skip nothing\n5 = skip the first 5\n\n/cancel — cancel this process",
        "fwd_bad_skip": "❌ Send a number, 0 or more.",
        "fwd_skip_big": "❌ Skip is larger than the selected range. Send a smaller number.",
        "fwd_check": "<b>DOUBLE CHECKING ⚠️</b>\n\nClick <b>Yes</b> only after checking this.\n\n★ <b>BOT:</b> {bot}\n★ <b>FROM:</b> {source}\n★ <b>TO:</b> {target}\n★ <b>SKIP:</b> {skip}\n★ <b>RANGE:</b> <code>{start}</code> → <code>{end}</code> ({count} posts)\n\n° This bot must be admin in the target chat.\n° If the source is private, /login first, or make this bot admin there too.",
        "fwd_check_fail": "\n\n❌ <b>Cannot start yet:</b>\n{problems}",
        "fwd_yes": "✅ Yes, start",
        "fwd_no": "❌ Cancel",
        "fwd_cancelled": "❌ Forward cancelled.",
        "fwd_started": "Forward started.",
    },
    "hi": {
        "queued": "⏳ Queue mein daal diya. Number <b>{n}</b>.\n<i>/cancel current kaam aur queue dono band karega.</i>",
        "queue_cleared": "✅ Queue saaf ho gayi.",
        "batch_cancelled": "✅ Batch cancel. Queue bhi saaf.",
        "nothing_active": "❌ Koi login, save, ya forward nahi chal raha.",
        "lang_set": "✅ Language <b>Hindi</b> set ho gayi.",
        "lang_pick": "<b>Language chuno</b>\n/lang en\n/lang hi",
        "copy_set": "✅ Copy mode: <b>{mode}</b>\n\n<b>dump</b> — sirf dump chat\n<b>both</b> — dump chat aur yeh private chat\n<b>pm</b> — sirf yeh private chat",
        "copy_usage": "<b>Usage:</b> <code>/copymode dump</code>, <code>both</code>, ya <code>pm</code>",
        "name_set": "✅ Rename template save ho gaya.\n<code>{template}</code>\n\nPlaceholders: <code>{filename}</code> <code>{index}</code> <code>{ext}</code>",
        "name_cleared": "✅ Rename template hata diya.",
        "name_usage": "<b>Usage:</b>\n<code>/setname MyFile_{index}</code>\n<code>/setname clear</code>",
        "fsub_need": "<b>Aage badhne ke liye required channel join karo.</b>",
        "fsub_join": "Join",
        "fwd_busy": "Forward pehle se chal raha hai. Band karne ke liye /cancel.",
        "fwd_setup_busy": "Forward setup khula hai. /cancel se band karo.",
        "fwd_need_dump": "<b>Dump chat set nahi hai.</b>\nBot ko channel mein admin banao, phir <code>/setchat -100...</code> ya <code>/setchat @channel</code>.",
        "fwd_choose": "<b>Forward Bot ⚡️</b>\n\n<b>❪ CHOOSE TARGET CHAT ❫</b>\n\nNeeche button se target chat chuno.\n/cancel — process cancel",
        "fwd_source": "<b>❪ SET SOURCE CHAT ❫</b>\n\nSaare posts chahiye to source ka <b>last message link</b> bhejo.\nKuch hi chahiye to range: <code>https://t.me/channel/1-100</code>\n\nPrivate: <code>https://t.me/c/123456/500</code>\n/cancel — process cancel",
        "fwd_bad_link": "❌ Telegram message link bhejo, ya /cancel.",
        "fwd_range_big": "❌ Yeh range <b>{count}</b> messages ki hai. Ek run mein max <b>{max}</b>.\nChhoti range bhejo. Jo post pehle ja chuki hai woh skip ho jayegi, isliye agli range se aage badh sakte ho.",
        "fwd_skip": "<b>❪ SET MESSAGE SKIP NUMBER ❫</b>\n\nShuru ke itne messages skip honge, baaki forward honge.\nDefault = 0\n\n0 = kuch skip nahi\n5 = pehle 5 skip\n\n/cancel — process cancel",
        "fwd_bad_skip": "❌ 0 ya usse bada number bhejo.",
        "fwd_skip_big": "❌ Skip range se bada hai. Chhota number bhejo.",
        "fwd_check": "<b>DOUBLE CHECKING ⚠️</b>\n\nYes tabhi dabana jab yeh check ho jaye.\n\n★ <b>BOT:</b> {bot}\n★ <b>FROM:</b> {source}\n★ <b>TO:</b> {target}\n★ <b>SKIP:</b> {skip}\n★ <b>RANGE:</b> <code>{start}</code> → <code>{end}</code> ({count} posts)\n\n° Target chat mein yeh bot admin hona chahiye.\n° Source private ho to pehle /login karo, ya bot ko wahan bhi admin banao.",
        "fwd_check_fail": "\n\n❌ <b>Abhi start nahi ho sakta:</b>\n{problems}",
        "fwd_yes": "✅ Yes, start",
        "fwd_no": "❌ Cancel",
        "fwd_cancelled": "❌ Forward cancel ho gaya.",
        "fwd_started": "Forward start ho gaya.",
    },
}


async def tr(user_id, key, **kwargs):
    lang = "en"
    try:
        lang = await db.get_lang(user_id)
    except Exception:
        lang = "en"
    text = STRINGS.get(lang, STRINGS["en"]).get(key) or STRINGS["en"].get(key) or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text
