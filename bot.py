import telebot
from telebot import types
import os
import datetime
import subprocess
import json

# --- الإعدادات ---
API_TOKEN = '8006782858:AAGwoCMq4WduKIi4FPK0gmk1y_xZe-urhpA'
ADMIN_ID = 7801575879
bot = telebot.TeleBot(API_TOKEN)

USERS_FILE = "users_db.json"
PROCS_FILE = "running_bots.json"
running_processes = {} 
user_db = {} 

# --- دوال البيانات ---
def load_data():
    global user_db
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f: user_db = json.load(f)
        except: user_db = {}

def save_data():
    with open(USERS_FILE, "w") as f: json.dump(user_db, f)

def save_running_procs():
    with open(PROCS_FILE, "w") as f:
        json.dump(list(running_processes.keys()), f)

def load_and_restart_procs():
    if os.path.exists(PROCS_FILE):
        try:
            with open(PROCS_FILE, "r") as f:
                to_restart = json.load(f)
                for file_name in to_restart:
                    if os.path.exists(file_name):
                        proc = subprocess.Popen(['python3', file_name])
                        running_processes[file_name] = proc
        except: pass

def get_remaining_time(user_id, expiry_str):
    if str(user_id) == str(ADMIN_ID): 
        return "مطور (مفعل دائماً) ⚡"
    if expiry_str == "waiting": 
        return "في انتظار أول ملف ⏳"
    try:
        expiry_date = datetime.datetime.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")
        remaining = expiry_date - datetime.datetime.now()
        if remaining.total_seconds() <= 0: 
            return "منتهي ❌"
        days = remaining.days
        hours, rem = divmod(remaining.seconds, 3600)
        minutes, seconds = divmod(rem, 60)
        return f"{days} يوم و {hours:02}:{minutes:02}:{seconds:02}" 
    except: 
        return "خطأ في قراءة الوقت"

def is_expired(user_id):
    uid = str(user_id)
    if uid == str(ADMIN_ID): return False
    if uid not in user_db or user_db[uid]["expiry"] == "waiting": return False
    expiry_date = datetime.datetime.strptime(user_db[uid]["expiry"], "%Y-%m-%d %H:%M:%S")
    return datetime.datetime.now() >= expiry_date

# --- لوحات المفاتيح ---
def main_inline_keyboard(user_id):
    uid = str(user_id)
    load_data()
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("📥 رفع ملف جديد", callback_data="upload_file"))
    markup.add(types.InlineKeyboardButton("🤖 البوتات المفعلة الخاصة", callback_data="user_list_my_bots"))
    
    if uid == str(ADMIN_ID):
        markup.add(types.InlineKeyboardButton("📂 ملفات السيرفر (أدمن)", callback_data="admin_list_all_files"),
                   types.InlineKeyboardButton("⭐ تفعيل شهري", callback_data="admin_activate_month"))
        markup.add(types.InlineKeyboardButton("🚫 إلغاء اشتراك", callback_data="admin_cancel_subscription"),
                   types.InlineKeyboardButton("🗑️ حذف ملف معين", callback_data="admin_delete_specific"))
        markup.add(types.InlineKeyboardButton("⚠️ حذف جميع الملفات (أدمن)", callback_data="admin_delete_all_files"))
    else:
      if user_db.get(uid, {}).get("type") == "month":
    markup.add(types.InlineKeyboardButton("👑 اشتراك VIP شهري فعال", callback_data="vip_status"))
    
    markup.add(types.InlineKeyboardButton("🛠️ الدعم الفني | تفعيل اشتراك", url="https://t.me/QW_LE1"))
    return markup

def file_control_keyboard(file_name):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🚀 تشغيل", callback_data=f"fastrun_{file_name}"),
        types.InlineKeyboardButton("🛑 إيقاف", callback_data=f"faststop_{file_name}")
    )
    markup.add(types.InlineKeyboardButton("🗑️ حذف الملف", callback_data=f"fastdel_{file_name}"))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.from_user.id)
    load_data()
    if uid not in user_db:
        user_db[uid] = {"type": "free", "expiry": "waiting"}
        save_data()
    
    info = user_db[uid]
    rank = "DEVELOPER ⚡" if uid == str(ADMIN_ID) else info['type'].upper()
    time_left = get_remaining_time(uid, info["expiry"])
    
    details = (
        f"👋 **أهلاً بك في نظام الاستضافة**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🆔 معرفك: `{uid}`\n"
        f"👤 الرتبة: `[{rank}]` \n"
        f"⏳ المتبقي: `{time_left}`\n"
        f"📅 الحالة: {'نشط ✅'}\n"
        f"━━━━━━━━━━━━━━━"
    )
    bot.send_message(message.chat.id, details, reply_markup=main_inline_keyboard(uid), parse_mode="Markdown")

# --- معالجة الضغطات ---
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    uid = str(call.from_user.id)
    load_data()

    if call.data == "admin_delete_all_files":
        if uid != str(ADMIN_ID): return
        files = [f for f in os.listdir('.') if f.endswith('.py') and "_" in f]
        count = 0
        for f in files:
            if f in running_processes:
                running_processes[f].terminate()
                del running_processes[f]
            os.remove(f)
            count += 1
        save_running_procs()
        bot.answer_callback_query(call.id, f"🛑 تم مسح {count} ملف بنجاح.", show_alert=True)

    elif call.data == "auto_extend_free":
        if not is_expired(uid) and user_db[uid]["expiry"] != "waiting" and uid != str(ADMIN_ID):
            bot.answer_callback_query(call.id, "⚠️ اشتراكك لا يزال فعالاً!", show_alert=True)
        else:
            new_expiry = datetime.datetime.now() + datetime.timedelta(days=1)
            user_db[uid] = {"type": "free", "expiry": new_expiry.strftime("%Y-%m-%d %H:%M:%S")}
            save_data()
            bot.answer_callback_query(call.id, "✅ تم التمديد لـ 24 ساعة.", show_alert=True)
            start(call.message)

    elif call.data == "user_list_my_bots":
        files = [f for f in os.listdir('.') if f.startswith(f"{uid}_")]
        if not files:
            bot.answer_callback_query(call.id, "⚠️ لا توجد ملفات مرفوعة.", show_alert=True)
            return
        for f in files:
            status = "🟢 مشغل" if f in running_processes else "🔴 متوقف"
            bot.send_message(call.message.chat.id, f"📄 ملف: `{f.replace(f'{uid}_', '')}`\nالحالة: {status}", 
                             reply_markup=file_control_keyboard(f), parse_mode="Markdown")

    elif call.data.startswith("fastrun_"):
        file_name = call.data.split("fastrun_")[1]
        if is_expired(uid):
            bot.answer_callback_query(call.id, "❌ صلاحيتك منتهية!", show_alert=True)
            return

        # --- ميزة تحديد عدد البوتات ---
        user_running_count = len([f for f in running_processes if f.startswith(uid)])
        user_type = user_db[uid]["type"]

        if uid != str(ADMIN_ID):
            if user_type == "free" and user_running_count >= 1:
                bot.answer_callback_query(call.id, "⚠️ الاشتراك المجاني يسمح بتشغيل بوت واحد فقط!", show_alert=True)
                return
            elif user_type == "month" and user_running_count >= 10:
                bot.answer_callback_query(call.id, "⚠️ اشتراك VIP يسمح بتشغيل 10 بوتات كحد أقصى!", show_alert=True)
                return

        if file_name not in running_processes:
            try:
                proc = subprocess.Popen(['python3', file_name])
                running_processes[file_name] = proc
                save_running_procs()
                bot.answer_callback_query(call.id, "🚀 تم التشغيل بنجاح.")
            except Exception as e: bot.answer_callback_query(call.id, f"❌ خطأ: {e}")
        else: bot.answer_callback_query(call.id, "⚠️ البوت مشغل بالفعل.")

    elif call.data.startswith("faststop_"):
        file_name = call.data.split("faststop_")[1]
        if file_name in running_processes:
            running_processes[file_name].terminate()
            del running_processes[file_name]
            save_running_procs()
            bot.answer_callback_query(call.id, "🛑 تم الإيقاف.")
        else: bot.answer_callback_query(call.id, "⚠️ البوت غير مشغل.")

    elif call.data.startswith("fastdel_"):
        file_name = call.data.split("fastdel_")[1]
        if os.path.exists(file_name):
            if file_name in running_processes:
                running_processes[file_name].terminate()
                del running_processes[file_name]
            os.remove(file_name)
            save_running_procs()
            bot.edit_message_text("🗑️ تم حذف الملف نهائياً.", call.message.chat.id, call.message.message_id)

    elif call.data == "admin_list_all_files":
        if uid != str(ADMIN_ID): return
        files = [f for f in os.listdir('.') if f.endswith('.py')]
        msg = "📂 ملفات السيرفر الحالية:\n" + "\n".join(files) if files else "السيرفر فارغ."
        bot.send_message(call.message.chat.id, msg)

    elif call.data == "admin_activate_month":
        if uid != str(ADMIN_ID): return
        msg = bot.send_message(call.message.chat.id, "👤 أرسل ID المستخدم لتفعيل VIP:")
        bot.register_next_step_handler(msg, admin_confirm_month)

    elif call.data == "admin_cancel_subscription":
        if uid != str(ADMIN_ID): return
        msg = bot.send_message(call.message.chat.id, "🚫 أرسل ID المستخدم لإلغاء تفعيله:")
        bot.register_next_step_handler(msg, admin_cancel_sub_process)

    elif call.data == "admin_delete_specific":
        if uid != str(ADMIN_ID): return
        msg = bot.send_message(call.message.chat.id, "🗑️ أرسل اسم الملف كاملاً (بالصيغة):")
        bot.register_next_step_handler(msg, admin_del_file_process)

    elif call.data == "upload_file":
        bot.send_message(call.message.chat.id, "📥 أرسل ملف البايثون (.py) الآن.")

# --- دوال الأدمن ---
def admin_confirm_month(message):
    target = message.text.strip()
    expiry = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    user_db[target] = {"type": "month", "expiry": expiry}
    save_data()
    bot.reply_to(message, f"✅ تم تفعيل {target} لمدة شهر (VIP - 10 بوتات).")

def admin_cancel_sub_process(message):
    target = message.text.strip()
    if target in user_db:
        user_db[target]["type"] = "free"
        user_db[target]["expiry"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_data()
        bot.reply_to(message, f"🚫 تم إلغاء تفعيل المستخدم {target}.")
    else: bot.reply_to(message, "❌ المستخدم غير موجود.")

def admin_del_file_process(message):
    f_name = message.text.strip()
    if os.path.exists(f_name):
        if f_name in running_processes:
            running_processes[f_name].terminate()
            del running_processes[f_name]
        os.remove(f_name)
        save_running_procs()
        bot.reply_to(message, f"🗑️ تم حذف الملف `{f_name}`.")
    else: bot.reply_to(message, "❌ الملف غير موجود.")

# --- استقبال الملفات ---
@bot.message_handler(content_types=['document'])
def handle_docs(message):
    uid = str(message.from_user.id)
    if not message.document.file_name.endswith('.py'):
        bot.reply_to(message, "❌ أرسل ملفات بايثون (.py) فقط.")
        return
    load_data()
    if user_db.get(uid, {}).get("expiry") == "waiting":
        user_db[uid]["expiry"] = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        save_data()
    
    file_name = f"{uid}_{message.document.file_name}"
    file_info = bot.get_file(message.document.file_id)
    downloaded = bot.download_file(file_info.file_path)
    with open(file_name, 'wb') as f: f.write(downloaded)
    bot.reply_to(message, f"✅ تم الحفظ. تحكم بملفك من زر (البوتات المفعلة الخاصة).")

if __name__ == "__main__":
    load_data()
    load_and_restart_procs()
    bot.infinity_polling()
