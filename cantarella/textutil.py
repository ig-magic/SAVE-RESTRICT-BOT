import os
from database.db import db


async def clean_text(user_id, text):
    """Apply /set_del_word and /set_repl_word. Empty input stays empty."""
    if not text:
        return text or ""
    try:
        words = await db.get_delete_words(user_id) or []
        repl = await db.get_replace_words(user_id) or {}
    except Exception:
        return text
    for word in words:
        if word:
            text = text.replace(word, "")
    for src, dst in repl.items():
        if src:
            text = text.replace(src, dst or "")
    return "\n".join(line.rstrip() for line in text.splitlines()).strip()


async def rename_path(user_id, path, index=1):
    """Rename a downloaded file using /setname, and strip delete-words from the name."""
    if not path or not os.path.exists(path):
        return path
    folder, original = os.path.split(path)
    stem, ext = os.path.splitext(original)
    template = await db.get_rename(user_id)
    if template:
        try:
            new_name = template.format(filename=stem, ext=ext, index=index, n=index)
        except Exception:
            new_name = template
        new_name = new_name.strip().replace("/", "_").replace("\\", "_")
        if ext and not os.path.splitext(new_name)[1]:
            new_name += ext
    else:
        new_name = original
    new_name = await clean_text(user_id, new_name) or new_name
    new_name = new_name.strip() or original
    dest = os.path.join(folder, new_name)
    if dest != path:
        if os.path.exists(dest):
            os.remove(dest)
        os.replace(path, dest)
    return dest
