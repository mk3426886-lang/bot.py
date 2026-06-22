#!/usr/bin/env python3
import os
import sys
import logging
import time
import subprocess
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ==================== التوكن والصلاحيات ====================
BOT_TOKEN = "8010944845:AAF6GMY9Lel6k4ZiKz8UP3wFMy_n7eyhVgI"
ADMIN_ID = 1425576247  # المالك الوحيد

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

start_time = time.time()

# ==================== أوامر البوت ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ **البوت شغال وجاهز!**\n"
        "━━━━━━━━━━━━━━━━\n"
        "🔹 `/start` - عرض هذه الرسالة\n"
        "🔹 `/stop` - إيقاف البوت (للمالك فقط)\n"
        "🔹 `/restart` - إعادة التشغيل (للمالك)\n"
        "🔹 `/status` - حالة البوت\n"
        "🔹 `/ping` - اختبار السرعة\n"
        "🔹 `/logs` - عرض آخر 10 سطور من السجلات (للمالك)\n"
        "━━━━━━━━━━━━━━━━\n"
        "🕒 الوقت الحالي: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ **أنت لست المالك!** هذا الأمر للمطور فقط.")
        return
    await update.message.reply_text("🛑 **جاري إيقاف البوت...** وداعاً 👋")
    logger.warning(f"⏹️ تم إيقاف البوت بواسطة المالك {user_id}")
    time.sleep(1)
    os._exit(0)

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ **أنت لست المالك!**")
        return
    await update.message.reply_text("🔄 **جاري إعادة التشغيل...**")
    logger.info("🔄 إعادة تشغيل البوت بأمر من المالك")
    os.execv(sys.executable, [sys.executable] + sys.argv)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uptime = time.time() - start_time
    hours = int(uptime // 3600)
    minutes = int((uptime % 3600) // 60)
    seconds = int(uptime % 60)
    await update.message.reply_text(
        "📊 **حالة البوت:**\n"
        f"✅ يعمل منذ: {hours}h {minutes}m {seconds}s\n"
        f"👤 المالك: {ADMIN_ID}\n"
        f"🕒 الآن: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        "📦 المكتبات: python-telegram-bot v20.7"
    )

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start = time.time()
    await update.message.reply_text("🏓 **Pong!**")
    end = time.time()
    await update.message.reply_text(f"⏱️ **زمن الاستجابة:** {(end - start) * 1000:.2f} مللي")

async def logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ **للمالك فقط!**")
        return
    try:
        result = subprocess.run(['tail', '-n', '10', 'bot.log'], capture_output=True, text=True, timeout=5)
        if result.stdout:
            await update.message.reply_text(f"📄 **آخر 10 سطور من السجلات:**\n```\n{result.stdout[:4000]}\n```", parse_mode='Markdown')
        else:
            await update.message.reply_text("📭 **لا يوجد سجلات بعد.**")
    except Exception as e:
        await update.message.reply_text(f"❌ **خطأ في قراءة السجلات:** {str(e)}")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"📨 **استلمت:** `{update.message.text}`", parse_mode='Markdown')

# ==================== التشغيل الرئيسي ====================
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("restart", restart))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("logs", logs))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    logger.info("🚀 **البوت شغال الآن!**")
    print(f"✅ البوت يعمل - المالك: {ADMIN_ID}")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
