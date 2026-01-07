#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ربات آوای سرزمین میانه - نسخه نهایی (بروزرسانی)
# ادمین: آیدی 8522374988

import logging, sqlite3, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from config import TOKEN, ADMIN_ID, DB_NAME

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- دیتابیس ----------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS music (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        file_id TEXT,
        category TEXT,
        album TEXT,
        rating_sum INTEGER DEFAULT 0,
        rating_count INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS ratings (
        user_id INTEGER,
        music_id INTEGER,
        rating INTEGER,
        PRIMARY KEY (user_id, music_id)
    )''')
    conn.commit()
    conn.close()

init_db()

# ---------- کیبوردهای اینلاین ----------
def glass_button(text, callback_data=None, url=None):
    if url:
        return InlineKeyboardButton(text, url=url)
    return InlineKeyboardButton(text, callback_data=callback_data)

def first_menu():
    keyboard = [
        [glass_button("1️⃣ منوی اصلی", "main_menu")],
        [glass_button("2️⃣ کانال سرزمین میانه", url="https://t.me/Earth_Middle")]
    ]
    return InlineKeyboardMarkup(keyboard)

def main_menu():
    keyboard = [
        [glass_button("📀 مجموعه آلبوم‌های موسیقی ارباب حلقه‌ها", "lotr_albums")],
        [glass_button("📀 مجموعه آلبوم‌های موسیقی هابیت", "hobbit_albums")],
        [glass_button("♨️ پادکست‌های داستان صوتی", "podcast_menu")],
        [glass_button("📌 حلقه‌های قدرت (فصل‌های ۱ و ۲)", "rings_of_power")],
        [glass_button("🎵 موسیقی طرفداران", "fan_music")],
        [glass_button("🎞 موسیقی متن انیمیشن‌های ارباب حلقه‌ها", "coming_soon")],
        [glass_button("🏆 رتبه‌بندی موسیقی‌ها", "ranking")]
    ]
    return InlineKeyboardMarkup(keyboard)

def lotr_albums_menu():
    keyboard = [
        [glass_button("📌 آلبوم موسیقی فیلم یاران حلقه (ارباب حلقه‌ها)🔥", "album_1")],
        [glass_button("📌 آلبوم موسیقی فیلم دو برج (ارباب حلقه‌ها)🔥", "album_2")],
        [glass_button("📌 آلبوم موسیقی فیلم بازگشت شاه (ارباب حلقه‌ها)🔥", "album_3")],
        [glass_button("🔙 بازگشت", "back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def hobbit_albums_menu():
    keyboard = [
        [glass_button("📌 آلبوم موسیقی فیلم یک سفر غیرمنتظره (هابیت)🔥", "album_4")],
        [glass_button("📌 آلبوم موسیقی فیلم برهوت اسماگ (هابیت)🔥", "album_5")],
        [glass_button("📌 آلبوم موسیقی فیلم نبرد پنج سپاه (هابیت)🔥", "album_6")],
        [glass_button("🔙 بازگشت", "back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ---------- دستور /start ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = f"سلام {user.first_name} به ربات آوای سرزمین میانه خوش آمدید!\n\nلطفاً انتخاب کنید:"
    await update.message.reply_text(welcome_text, reply_markup=first_menu())

# ---------- مدیریت کلیک منوها ----------
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    # منوی اصلی
    if data == "main_menu":
        await query.edit_message_text("منوی اصلی:", reply_markup=main_menu())
        return
    if data == "lotr_albums":
        await query.edit_message_text("مجموعه آلبوم‌های موسیقی ارباب حلقه‌ها:", reply_markup=lotr_albums_menu())
        return
    if data == "hobbit_albums":
        await query.edit_message_text("مجموعه آلبوم‌های موسیقی هابیت:", reply_markup=hobbit_albums_menu())
        return

    # امتیازدهی (۱ تا ۸)
    if data.startswith("rate_"):
        rating = int(data.split("_")[1])
        if 'pending_rate' in context.user_data:
            music_id = context.user_data.pop('pending_rate')
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT rating FROM ratings WHERE user_id=? AND music_id=?", (user_id, music_id))
            old_row = c.fetchone()
            if old_row:
                old_rating = old_row[0]
                c.execute("UPDATE music SET rating_sum = rating_sum - ? + ? WHERE id=?",
                          (old_rating, rating, music_id))
                c.execute("UPDATE ratings SET rating=? WHERE user_id=? AND music_id=?",
                          (rating, user_id, music_id))
            else:
                c.execute("UPDATE music SET rating_sum = rating_sum + ?, rating_count = rating_count + 1 WHERE id=?",
                          (rating, music_id))
                c.execute("INSERT INTO ratings VALUES (?, ?, ?)", (user_id, music_id, rating))
            conn.commit()
            conn.close()
            await query.answer(f"✅ امتیاز {rating} ثبت شد!", show_alert=True)
            await query.message.delete()
        return

    # آلبوم‌ها
    if data.startswith("album_"):
        album_id = int(data.split("_")[1])
        await show_tracks(update, context, album_id)
        return

    # ترک‌های آلبوم
    if data.startswith("track_"):
        parts = data.split("_")
        album_id = int(parts[1])
        track_index = int(parts[2])
        await handle_track(update, context, album_id, track_index)
        return

    # آپلود توسط ادمین (برای آلبوم‌ها)
    if data.startswith("upload_album_"):
        parts = data.split("_")
        album_id = int(parts[2])
        track_index = int(parts[3])
        context.user_data['pending_upload'] = ('album', album_id, track_index)
        await query.edit_message_text("فایل موسیقی را ارسال کن (صوتی):")
        return

    # پادکست
    if data == "podcast_menu":
        await podcast_menu(update, context)
        return
    if data.startswith("podcast_"):
        pid = int(data.split("_")[1])
        await handle_podcast(update, context, pid)
        return
    if data.startswith("upload_podcast_"):
        pid = int(data.split("_")[2])
        context.user_data['pending_upload'] = ('podcast', pid)
        await query.edit_message_text("فایل پادکست را ارسال کن (صوتی):")
        return

    # کتاب صوتی هابیت زبان اصلی (۲۱ فصل)
    if data.startswith("hobbit_audio_"):
        chapter = int(data.split("_")[2])
        await handle_hobbit_audio(update, context, chapter)
        return
    if data.startswith("upload_hobbit_audio_"):
        chapter = int(data.split("_")[3])
        context.user_data['pending_upload'] = ('hobbit_audio', chapter)
        await query.edit_message_text("فایل این فصل را ارسال کن (صوتی):")
        return

    # حلقه‌های قدرت
    if data == "rings_of_power":
        await rings_menu(update, context)
        return
    if data.startswith("rop_season_"):
        season = int(data.split("_")[2])
        await rop_episodes(update, context, season)
        return
    if data.startswith("rop_ep_"):
        parts = data.split("_")
        season = int(parts[2])
        episode = int(parts[3])
        await handle_rop_season1(update, context, season, episode)
        return
    if data.startswith("rop_track_"):
        parts = data.split("_")
        season = int(parts[2])
        episode = int(parts[3])
        track_index = int(parts[4])
        await handle_rop_track(update, context, season, episode, track_index)
        return
    if data.startswith("upload_rop_track_"):
        parts = data.split("_")
        season = int(parts[3])
        episode = int(parts[4])
        track_index = int(parts[5])
        context.user_data['pending_upload'] = ('rop_track', season, episode, track_index)
        await query.edit_message_text("فایل این ترک را ارسال کن (صوتی):")
        return
    if data.startswith("upload_rop_"):
        parts = data.split("_")
        season = int(parts[2])
        episode = int(parts[3])
        context.user_data['pending_upload'] = ('rop', season, episode)
        await query.edit_message_text("فایل موسیقی این قسمت را ارسال کن (صوتی):")
        return

    # موسیقی طرفداران
    if data == "fan_music":
        await fan_music_menu(update, context)
        return
    if data.startswith("fan_"):
        fid = int(data.split("_")[1])
        await handle_fan_music(update, context, fid)
        return
    if data.startswith("upload_fan_"):
        fid = int(data.split("_")[2])
        context.user_data['pending_upload'] = ('fan', fid)
        await query.edit_message_text("فایل موسیقی را ارسال کن (صوتی):")
        return

    # انیمیشن قدیمی (در دست ساخت)
    if data == "coming_soon":
        await query.answer("این بخش در بروزرسانی آینده فعال خواهد شد.", show_alert=True)
        return

    # رتبه‌بندی شیشه‌ای
    if data == "ranking":
        await show_ranking_glass(update, context)
        return

    # بازگشت
    if data == "back_main":
        await query.edit_message_text("منوی اصلی:", reply_markup=main_menu())
        return

# ---------- نمایش ترک‌های آلبوم ----------
album_tracks = {
    1: [
        "The Prophecy 3:55", "Concerning Hobbits 2:55", "The Shadow of the Past 3:32",
        "The Treason of Isengard 4:00", "The Black Rider 2:48", "At the Sign of the Prancing Pony 3:14",
        "A Knife in the Dark 3:34", "Flight to the Ford 4:14", "Many Meetings 3:05",
        "The Council of Elrond 3:49", "The Ring Goes South 2:03", "A Journey in the Dark 4:20",
        "The Bridge of Khazad-dûm 5:57", "Lothlórien 4:33", "The Great River 2:42",
        "Amon Hen 5:02", "The Breaking of the Fellowship 7:20", "May It Be 4:19"
    ],
    2: [
        "Foundations of Stone 3:51", "The Taming of Sméagol 2:48", "The Riders of Rohan 4:05",
        "The Passage of the Marshes 2:46", "The Uruk-hai 2:58", "The King of the Golden Hall 3:49",
        "The Black Gate Is Closed 3:17", "Evenstar 3:15", "The White Rider 2:28",
        "Treebeard 2:43", "The Leave Taking 3:41", "Helm's Deep 3:53",
        "The Forbidden Pool 5:27", "Breath of Life 5:07", "The Hornburg 4:36",
        "Forth Eorlingas 3:15", "Isengard Unleashed 5:01", "Samwise the Brave 3:46",
        "Gollum's Song 5:51", "Farewell to Lórien 4:37"
    ],
    3: [
        "A Storm Is Coming 2:52", "Hope and Memory 1:45", "Minas Tirith 3:37",
        "The White Tree 3:25", "The Steward of Gondor 3:53", "Minas Morgul 1:58",
        "The Ride of the Rohirrim 2:08", "Twilight and Shadow 3:30", "Cirith Ungol 1:44",
        "Andúril 2:35", "Shelob's Lair 4:07", "Ash and Smoke 3:25",
        "The Fields of the Pelennor 3:26", "Hope Fails 2:20", "The Black Gate Opens 4:01",
        "The End of All Things 5:12", "The Return of the King 10:14", "The Grey Havens 5:59",
        "Into the West 5:47"
    ],
    4: [
        "My Dear Frodo 8:03", "Old Friends (extended version) 5:01", "An Unexpected Party (extended version) 4:09",
        "Blunt the Knives 1:01", "Axe or Sword? 5:59", "Misty Mountains 1:42",
        "The Adventure Begins 2:05", "The World is Ahead 2:20", "An Ancient Enemy 4:57",
        "Radagast the Brown (extended version) 6:39", "The Trollshaws 2:09", "Roast Mutton (extended version) 4:57",
        "A Troll-hoard 2:39", "The Hill of Sorcery 3:51", "Warg-Scouts 3:02",
        "The Hidden Valley 3:49", "Moon Runes (extended version) 3:39", "The Defiler 1:14",
        "The White Council (extended version) 9:41", "Over Hill 3:44", "A Thunder Battle 3:55",
        "Under Hill 1:55", "Riddles in the Dark 5:21", "Brass Buttons 7:38",
        "Out of the Frying-Pan 5:55", "A Good Omen 5:47", "Song of the Lonely Mountain (extended version) 6:01",
        "Dreaming of Bag End 1:47", "A Very Respectable Hobbit 1:22", "Erebor 1:19",
        "The Dwarf Lords 2:01", "The Edge of the Wild 3:34"
    ],
    5: [
        "The Quest for Erebor", "Wilderland", "A Necromancer", "The House of Beorn",
        "Mirkwood", "Flies and Spiders", "The Woodland Realm", "Feast Of Starlight",
        "Barrels Out Of Bond", "The Forest River", "Bard, A Man Of Lake-Town",
        "The High Fells", "The Nature Of Evil", "Protector Of The Common Folk",
        "Thrice Welcome", "Girion, Lord Of Dale", "Durin's Folk", "In The Shadow Of The Mountain",
        "A Spell Of Concealment", "On The Doorstep", "The Courage Of Hobbits",
        "Inside Information", "Kingsfoil", "A Liar And A Thief", "The Hunters",
        "Smaug", "My Armour Is Iron", "I See Fire", "Beyond The Forest"
    ],
    6: [
        "Fire and Water", "Shores of the Long Lake", "Beyond Sorrow and Grief",
        "Guardians of the Three", "The Ruins of Dale", "The Gathering of the Clouds",
        "Mithril", "Bred for War", "A Thief in the Night", "The Clouds Burst",
        "Battle for the Mountain", "The Darkest Hour", "Sons of Durin",
        "The Fallen", "Ravenhill", "To the Death", "Courage and Wisdom",
        "The Return Journey", "There and Back Again", "The Last Goodbye",
        "Ironfoot", "Dragon Sickness", "Thráin"
    ]
}

async def show_tracks(update: Update, context: ContextTypes.DEFAULT_TYPE, album_id):
    query = update.callback_query
    tracks = album_tracks.get(album_id, [])
    keyboard = []
    for i, track in enumerate(tracks):
        keyboard.append([glass_button(f"{i+1}. {track}", f"track_{album_id}_{i}")])
    keyboard.append([glass_button("🔙 بازگشت", "back_main")])
    await query.edit_message_text(f"آلبوم {album_id} - ترک‌ها:", reply_markup=InlineKeyboardMarkup(keyboard))

# ---------- ارسال ترک آلبوم ----------
async def handle_track(update: Update, context: ContextTypes.DEFAULT_TYPE, album_id, track_index):
    query = update.callback_query
    user_id = query.from_user.id
    tracks = album_tracks.get(album_id, [])
    if track_index >= len(tracks):
        await query.answer("ترک یافت نشد!")
        return
    track_title = tracks[track_index]
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, file_id FROM music WHERE title=? AND album=?", (track_title, f"album_{album_id}"))
    row = c.fetchone()
    conn.close()
    if row:
        music_id, file_id = row[0], row[1]
        caption = f"{track_title}\n🔗 @Earth_Middle"
        await context.bot.send_audio(chat_id=query.message.chat_id, audio=file_id, caption=caption)
        context.user_data['pending_rate'] = music_id
        keyboard = [[glass_button(str(i), f"rate_{i}") for i in range(1, 9)]]
        await query.message.reply_text(
            f"چه امتیازی به «{track_title}» میدهید؟ (۱-۸)",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        msg = f"ترک «{track_title}» هنوز آپلود نشده."
        if user_id in ADMIN_ID:
            keyboard = [[glass_button("➕ آپلود این ترک", f"upload_album_{album_id}_{track_index}")]]
            await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.answer(msg, show_alert=True)

# ---------- پادکست ----------
podcast_list = [
    "کتاب صوتی ارباب حلقه‌ها: یاران حلقه🔥",
    "کتاب صوتی ارباب حلقه‌ها: دو برج🔥",
    "کتاب صوتی ارباب حلقه‌ها: بازگشت شاه🔥",
    "کتاب صوتی هابیت!🔥",
    "کتاب صوتی سیلماریلیون!🔥",
    "کتاب صوتی هابیت زبان اصلی – راوی: اندی سرکیس"
]
async def podcast_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    keyboard = []
    for i, podcast in enumerate(podcast_list):
        keyboard.append([glass_button(podcast, f"podcast_{i}")])
    keyboard.append([glass_button("🔙 بازگشت", "back_main")])
    await query.edit_message_text("پادکست‌های داستان صوتی:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_podcast(update: Update, context: ContextTypes.DEFAULT_TYPE, pid):
    query = update.callback_query
    user_id = query.from_user.id
    if pid >= len(podcast_list):
        await query.answer("پادکست یافت نشد!")
        return
    title = podcast_list[pid]
    # کتاب صوتی هابیت زبان اصلی (۲۱ فصل)
    if pid == 5:
        await hobbit_audio_chapters(update, context)
        return
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, file_id FROM music WHERE title=? AND category='podcast'", (title,))
    row = c.fetchone()
    conn.close()
    if row:
        music_id, file_id = row[0], row[1]
        caption = f"{title}\n🔗 @Earth_Middle"
        await context.bot.send_audio(chat_id=query.message.chat_id, audio=file_id, caption=caption)
        context.user_data['pending_rate'] = music_id
        keyboard = [[glass_button(str(i), f"rate_{i}") for i in range(1, 9)]]
        await query.message.reply_text(
            f"چه امتیازی به «{title}» میدهید؟ (۱-۸)",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        msg = f"پادکست «{title}» هنوز آپلود نشده."
        if user_id in ADMIN_ID:
            keyboard = [[glass_button("➕ آپلود این پادکست", f"upload_podcast_{pid}")]]
            await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.answer(msg, show_alert=True)

# ---------- کتاب صوتی هابیت زبان اصلی (۲۱ فصل) ----------
async def hobbit_audio_chapters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    keyboard = []
    for i in range(1, 22):
        keyboard.append([glass_button(f"فصل {i}", f"hobbit_audio_{i}")])
    keyboard.append([glass_button("🔙 بازگشت", "podcast_menu")])
    await query.edit_message_text("کتاب صوتی هابیت زبان اصلی – راوی: اندی سرکیس\n(۲۱ فصل)", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_hobbit_audio(update: Update, context: ContextTypes.DEFAULT_TYPE, chapter):
    query = update.callback_query
    user_id = query.from_user.id
    title = f"کتاب صوتی هابیت زبان اصلی – فصل {chapter} – راوی: اندی سرکیس"
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, file_id FROM music WHERE title=? AND category='hobbit_audio'", (title,))
    row = c.fetchone()
    conn.close()
    if row:
        music_id, file_id = row[0], row[1]
        caption = f"{title}\n🔗 @Earth_Middle"
        await context.bot.send_audio(chat_id=query.message.chat_id, audio=file_id, caption=caption)
        context.user_data['pending_rate'] = music_id
        keyboard = [[glass_button(str(i), f"rate_{i}") for i in range(1, 9)]]
        await query.message.reply_text(
            f"چه امتیازی به «{title}» میدهید؟ (۱-۸)",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        msg = f"فصل {chapter} هنوز آپلود نشده."
        if user_id in ADMIN_ID:
            keyboard = [[glass_button(f"➕ آپلود فصل {chapter}", f"upload_hobbit_audio_{chapter}")]]
            await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.answer(msg, show_alert=True)

# ---------- حلقه‌های قدرت ----------
rop_season1_track_counts = {
    1: 9, 2: 10, 3: 10, 4: 8, 5: 10, 6: 6, 7: 10, 8: 8
}

async def rings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    keyboard = [
        [glass_button("فصل اول", "rop_season_1")],
        [glass_button("فصل دوم", "rop_season_2")],
        [glass_button("🔙 بازگشت", "back_main")]
    ]
    await query.edit_message_text("حلقه‌های قدرت:", reply_markup=InlineKeyboardMarkup(keyboard))

async def rop_episodes(update: Update, context: ContextTypes.DEFAULT_TYPE, season):
    query = update.callback_query
    if season == 1:
        keyboard = [[glass_button(f"قسمت {i}", f"rop_ep_{season}_{i}")] for i in range(1, 9)]
    else:
        keyboard = [[glass_button(f"قسمت {i}", f"rop_ep_{season}_{i}")] for i in range(1, 9)]
    keyboard.append([glass_button("🔙 بازگشت", "rings_of_power")])
    await query.edit_message_text(f"فصل {season} - انتخاب قسمت:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_rop_season1(update: Update, context: ContextTypes.DEFAULT_TYPE, season, episode):
    query = update.callback_query
    user_id = query.from_user.id
    if season == 1 and episode in rop_season1_track_counts:
        track_count = rop_season1_track_counts[episode]
        keyboard = []
        for i in range(1, track_count + 1):
            keyboard.append([glass_button(f"ترک {i}", f"rop_track_{season}_{episode}_{i-1}")])
        keyboard.append([glass_button("🔙 بازگشت", f"rop_season_{season}")])
        await query.edit_message_text(f"فصل {season} قسمت {episode} - ترک‌ها:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        title = f"حلقه‌های قدرت فصل {season} قسمت {episode}"
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id, file_id FROM music WHERE title=? AND category='rop'", (title,))
        row = c.fetchone()
        conn.close()
        if row:
            music_id, file_id = row[0], row[1]
            caption = f"{title}\n🔗 @Earth_Middle"
            await context.bot.send_audio(chat_id=query.message.chat_id, audio=file_id, caption=caption)
            context.user_data['pending_rate'] = music_id
            keyboard = [[glass_button(str(i), f"rate_{i}") for i in range(1, 9)]]
            await query.message.reply_text(
                f"چه امتیازی به «{title}» میدهید؟ (۱-۸)",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            msg = f"موسیقی‌های «{title}» هنوز آپلود نشده."
            if user_id in ADMIN_ID:
                keyboard = [[glass_button("➕ آپلود موسیقی این قسمت", f"upload_rop_{season}_{episode}")]]
                await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                await query.answer(msg, show_alert=True)

async def handle_rop_track(update: Update, context: ContextTypes.DEFAULT_TYPE, season, episode, track_index):
    query = update.callback_query
    user_id = query.from_user.id
    track_num = track_index + 1
    title = f"حلقه‌های قدرت فصل {season} قسمت {episode} – ترک {track_num}"
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, file_id FROM music WHERE title=? AND category='rop_track'", (title,))
    row = c.fetchone()
    conn.close()
    if row:
        music_id, file_id = row[0], row[1]
        caption = f"{title}\n🔗 @Earth_Middle"
        await context.bot.send_audio(chat_id=query.message.chat_id, audio=file_id, caption=caption)
        context.user_data['pending_rate'] = music_id
        keyboard = [[glass_button(str(i), f"rate_{i}") for i in range(1, 9)]]
        await query.message.reply_text(
            f"چه امتیازی به «{title}» میدهید؟ (۱-۸)",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        msg = f"ترک «{title}» هنوز آپلود نشده."
        if user_id in ADMIN_ID:
            keyboard = [[glass_button("➕ آپلود این ترک", f"upload_rop_track_{season}_{episode}_{track_index}")]]
            await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.answer(msg, show_alert=True)

# ---------- موسیقی طرفداران ----------
fan_music_list = [
    "تم موسیقی گوتموگ، فرمانروای بالروگ‌ها / مازیار شاهین‌مقدم",
    "تم موسیقی «آناتار»، خداوندگار هبه‌ها / مازیار شاهین‌مقدم",
    "تم موسیقی «گوندولین»، شهر پنهان نولدور / مازیار شاهین‌مقدم",
    "تم موسیقی «گلورفیندل»، دلاور مشهور نولدور / مازیار شاهین‌مقدم",
    "تم موسیقی «والینور»، سرزمین قدسی / مازیار شاهین‌مقدم",
    "تم موسیقی «ملیانِ مایا»، ملکهٔ دوریات / مازیار شاهین‌مقدم",
    "تم موسیقی «اونگولیانت»، عنکبوت غول‌پیکر / مازیار شاهین‌مقدم",
    "تم موسیقی «اشک سیم‌گون، برن و لوتین» / مازیار شاهین‌مقدم",
    "تم موسیقی «دوریاث» قلمرو الف‌های سیندار / مازیار شاهین‌مقدم"
]
async def fan_music_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    keyboard = [[glass_button(track, f"fan_{i}")] for i, track in enumerate(fan_music_list)]
    keyboard.append([glass_button("🔙 بازگشت", "back_main")])
    await query.edit_message_text("موسیقی طرفداران:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_fan_music(update: Update, context: ContextTypes.DEFAULT_TYPE, fid):
    query = update.callback_query
    user_id = query.from_user.id
    if fid >= len(fan_music_list):
        await query.answer("موسیقی یافت نشد!")
        return
    title = fan_music_list[fid]
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, file_id FROM music WHERE title=? AND category='fan'", (title,))
    row = c.fetchone()
    conn.close()
    if row:
        music_id, file_id = row[0], row[1]
        caption = f"{title}\n🔗 @Earth_Middle"
        await context.bot.send_audio(chat_id=query.message.chat_id, audio=file_id, caption=caption)
        context.user_data['pending_rate'] = music_id
        keyboard = [[glass_button(str(i), f"rate_{i}") for i in range(1, 9)]]
        await query.message.reply_text(
            f"چه امتیازی به «{title}» میدهید؟ (۱-۸)",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        msg = f"موسیقی «{title}» هنوز آپلود نشده."
        if user_id in ADMIN_ID:
            keyboard = [[glass_button("➕ آپلود این موسیقی", f"upload_fan_{fid}")]]
            await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.answer(msg, show_alert=True)

# ---------- رتبه‌بندی شیشه‌ای ----------
async def show_ranking_glass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT title, rating_sum, rating_count 
        FROM music 
        WHERE rating_count > 0 
        ORDER BY rating_sum DESC, rating_count DESC 
        LIMIT 20
    """)
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        text = "🏆 *رتبه‌بندی موسیقی‌ها*\n\n"
        text += "```\n"
        text += "   هنوز امتیازی ثبت نشده.\n"
        text += "```"
    else:
        text = "🏆 *رتبه‌بندی موسیقی‌ها*\n\n"
        text += "```\n"
        for i, (title, sum_r, count) in enumerate(rows):
            stars = "⭐" * min(5, int(sum_r // (count * 1.6))) if count > 0 else ""
            line = f"{i+1:2}. {stars} ({sum_r:3} امتیاز، {count:2} رأی)\n   {title[:35]}"
            if len(title) > 35:
                line += "..."
            text += line + "\n\n"
        text += "```"
    
    keyboard = [[glass_button("🔙 بازگشت", "back_main")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# ---------- دریافت فایل از ادمین ----------
async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_ID:
        return
    if 'pending_upload' not in context.user_data:
        return
    data = context.user_data.pop('pending_upload')
    file_id = update.message.audio.file_id
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    title = ""
    if data[0] == 'album':
        _, album_id, track_index = data
        tracks = album_tracks.get(album_id, [])
        if track_index >= len(tracks):
            return
        title = tracks[track_index]
        album = f"album_{album_id}"
        c.execute("INSERT OR REPLACE INTO music (title, file_id, album, category) VALUES (?, ?, ?, ?)",
                  (title, file_id, album, 'album'))
    elif data[0] == 'podcast':
        _, pid = data
        if pid >= len(podcast_list):
            return
        title = podcast_list[pid]
        c.execute("INSERT OR REPLACE INTO music (title, file_id, category) VALUES (?, ?, ?)",
                  (title, file_id, 'podcast'))
    elif data[0] == 'rop':
        _, season, episode = data
        title = f"حلقه‌های قدرت فصل {season} قسمت {episode}"
        c.execute("INSERT OR REPLACE INTO music (title, file_id, category) VALUES (?, ?, ?)",
                  (title, file_id, 'rop'))
    elif data[0] == 'rop_track':
        _, season, episode, track_index = data
        track_num = track_index + 1
        title = f"حلقه‌های قدرت فصل {season} قسمت {episode} – ترک {track_num}"
        c.execute("INSERT OR REPLACE INTO music (title, file_id, category) VALUES (?, ?, ?)",
                  (title, file_id, 'rop_track'))
    elif data[0] == 'fan':
        _, fid = data
        if fid >= len(fan_music_list):
            return
        title = fan_music_list[fid]
        c.execute("INSERT OR REPLACE INTO music (title, file_id, category) VALUES (?, ?, ?)",
                  (title, file_id, 'fan'))
    elif data[0] == 'hobbit_audio':
        _, chapter = data
        title = f"کتاب صوتی هابیت زبان اصلی – فصل {chapter} – راوی: اندی سرکیس"
        c.execute("INSERT OR REPLACE INTO music (title, file_id, category) VALUES (?, ?, ?)",
                  (title, file_id, 'hobbit_audio'))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ فایل «{title}» با موفقیت ذخیره شد.")
    try:
        await update.message.delete()
    except:
        pass

# ---------- دستور announce (فقط ادمین) ----------
async def announce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_ID:
        await update.message.reply_text("❌ این دستور فقط برای ادمین است.")
        return
    context.user_data['awaiting_announce'] = True
    await update.message.reply_text("📢 لطفاً پیام اعلان را ارسال کنید:")

async def handle_announce_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_ID:
        return
    if 'awaiting_announce' not in context.user_data:
        return
    del context.user_data['awaiting_announce']
    message = update.message.text
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT DISTINCT user_id FROM ratings")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    total = len(users)
    success = 0
    await update.message.reply_text(f"📨 شروع ارسال به {total} کاربر...")
    for uid in users:
        try:
            await context.bot.send_message(chat_id=uid, text=f"📢 اعلان از ربات آوای سرزمین میانه:\n\n{message}")
            success += 1
            await asyncio.sleep(0.5)  # جلوگیری از محدودیت تلگرام
        except Exception as e:
            logger.warning(f"خطا در ارسال به {uid}: {e}")
    await update.message.reply_text(f"✅ اعلان به {success} از {total} کاربر ارسال شد.")

# ---------- تنظیمات ربات ----------
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("announce", announce))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_announce_text))
    app.add_handler(MessageHandler(filters.AUDIO, handle_audio))
    logger.info("ربات آوای سرزمین میانه در حال اجراست...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
