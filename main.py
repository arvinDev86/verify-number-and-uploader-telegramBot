import telebot
from telebot import types
import database  # ایمپورت کردن فایل دیتابیس که خودمان ساختیم

# --- تنظیمات ---
TOKEN = '8349714294:AAHqmbo3cl5b8BWxDmmApKM8svm-0mLuMgA'
ADMIN_PASSWORD = '12345'  # رمز ادمین
bot = telebot.TeleBot(TOKEN)

# راه اندازی دیتابیس
database.init_db()

# کش محتوا (خواندن اولیه)
archive_cache = database.get_all_content()

# لیست ادمین‌های لاگین شده
admin_sessions = []

# --- منوی اصلی کاربر ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    user_data = database.get_user(user_id)

    if user_data and user_data[3]:
        bot.send_message(user_id, f"سلام {message.chat.first_name}، به آرشیو خوش آمدید.")
        show_user_menu(user_id)
    else:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        btn_phone = types.KeyboardButton(text="📱 ارسال شماره و ورود", request_contact=True)
        markup.add(btn_phone)
        bot.send_message(user_id, "برای مشاهده آرشیو، لطفاً شماره خود را تایید کنید.", reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    user_id = message.chat.id
    if message.contact and message.contact.user_id == user_id:
        database.add_user(user_id, message.chat.first_name, message.chat.username, message.contact.phone_number)
        bot.send_message(user_id, "✅ ثبت نام انجام شد.", reply_markup=types.ReplyKeyboardRemove())
        show_user_menu(user_id)
    else:
        bot.send_message(user_id, "لطفا شماره خودتان را ارسال کنید.")

def show_user_menu(chat_id):
    global archive_cache  # <--- اصلاح شده: همیشه در خط اول تابع
    
    # بروزرسانی کش از دیتابیس برای اطمینان
    archive_cache = database.get_all_content()
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    if archive_cache:
        markup.add(*archive_cache.keys())
        bot.send_message(chat_id, "📂 دسته‌بندی مورد نظر را انتخاب کنید:", reply_markup=markup)
    else:
        bot.send_message(chat_id, "📭 آرشیو در حال حاضر خالی است.")

# --- هندلر ارسال محتوا به کاربر ---
@bot.message_handler(func=lambda message: message.text in archive_cache.keys())
def send_archive_content(message):
    user_id = message.chat.id
    # چک کردن ثبت نام کاربر
    user_data = database.get_user(user_id)
    if not user_data or not user_data[3]:
        bot.send_message(user_id, "لطفا ابتدا /start بزنید.")
        return

    category = message.text
    content = archive_cache[category]
    
    bot.send_message(user_id, f"در حال ارسال {category} ...")
    
    try:
        if content['type'] == 'text':
            bot.send_message(user_id, content['data'])
        elif content['type'] == 'photo':
            bot.send_photo(user_id, content['data'])
        elif content['type'] == 'video':
            bot.send_video(user_id, content['data'])
        elif content['type'] == 'document':
            bot.send_document(user_id, content['data'])
        elif content['type'] == 'audio':
            bot.send_audio(user_id, content['data'])
    except Exception as e:
        bot.send_message(user_id, f"خطا در ارسال فایل: {e}")

# ==========================================
#               بخش پنل ادمین
# ==========================================

@bot.message_handler(commands=['admin'])
def admin_login(message):
    msg = bot.send_message(message.chat.id, "🔒 لطفاً رمز عبور ادمین را وارد کنید:")
    bot.register_next_step_handler(msg, verify_password)

def verify_password(message):
    if message.text == ADMIN_PASSWORD:
        admin_sessions.append(message.chat.id)
        show_admin_panel(message.chat.id)
    else:
        bot.send_message(message.chat.id, "❌ رمز عبور اشتباه است.")

def show_admin_panel(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("👥 مشاهده کاربران", "➕ افزودن فایل", "🗑 حذف فایل", "🔙 خروج")
    bot.send_message(chat_id, "🔧 به پنل مدیریت خوش آمدید. گزینه مورد نظر را انتخاب کنید:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.chat.id in admin_sessions)
def admin_actions(message):
    chat_id = message.chat.id
    text = message.text

    if text == "🔙 خروج":
        if chat_id in admin_sessions:
            admin_sessions.remove(chat_id)
        bot.send_message(chat_id, "خروج از پنل مدیریت.", reply_markup=types.ReplyKeyboardRemove())
        send_welcome(message) 
    
    elif text == "👥 مشاهده کاربران":
        users = database.get_all_users()
        if not users:
            bot.send_message(chat_id, "هیچ کاربری ثبت نشده است.")
        else:
            report = "📋 لیست کاربران:\n\n"
            for u in users:
                uname = f"@{u[1]}" if u[1] else "ندارد"
                report += f"👤 {u[0]}\n🆔 {uname}\n📞 {u[2]}\n----------------\n"
            
            if len(report) > 4000:
                bot.send_document(chat_id, report.encode(), visible_file_name="users.txt")
            else:
                bot.send_message(chat_id, report)

    elif text == "➕ افزودن فایل":
        msg = bot.send_message(chat_id, "✏️ نام دسته‌بندی (نام دکمه) را بنویسید:\n(مثلاً: کتاب ریاضی)")
        bot.register_next_step_handler(msg, admin_get_category_name)

    elif text == "🗑 حذف فایل":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        # استفاده از متغیر سراسری بدون تغییر آن، نیازی به global ندارد
        current_cats = list(archive_cache.keys())
        if not current_cats:
            bot.send_message(chat_id, "هیچ فایلی برای حذف وجود ندارد.")
            return
        markup.add(*current_cats)
        markup.add("🔙 برگشت به منو")
        msg = bot.send_message(chat_id, "کدام دسته را حذف کنم؟", reply_markup=markup)
        bot.register_next_step_handler(msg, admin_delete_category)
    
    else:
        show_admin_panel(chat_id)

# --- مراحل افزودن فایل ---
def admin_get_category_name(message):
    category_name = message.text
    msg = bot.send_message(message.chat.id, f"📥 حالا فایل مربوط به '{category_name}' را بفرستید:")
    bot.register_next_step_handler(msg, admin_save_content, category_name)

def admin_save_content(message, category_name):
    global archive_cache  # <--- اصلاح شده: همیشه در خط اول تابع

    content_type = message.content_type
    content_data = None

    if content_type == 'text':
        content_data = message.text
    elif content_type == 'photo':
        content_data = message.photo[-1].file_id
    elif content_type == 'video':
        content_data = message.video.file_id
    elif content_type == 'document':
        content_data = message.document.file_id
    elif content_type == 'audio':
        content_data = message.audio.file_id
    else:
        bot.send_message(message.chat.id, "❌ فرمت فایل پشتیبانی نمی‌شود.")
        show_admin_panel(message.chat.id)
        return

    database.add_content(category_name, content_data, content_type)
    
    # آپدیت متغیر سراسری
    archive_cache = database.get_all_content()

    bot.send_message(message.chat.id, f"✅ دسته '{category_name}' با موفقیت ذخیره شد.")
    show_admin_panel(message.chat.id)

# --- مراحل حذف فایل ---
def admin_delete_category(message):
    global archive_cache  # <--- اصلاح شده: همیشه در خط اول تابع

    if message.text == "🔙 برگشت به منو":
        show_admin_panel(message.chat.id)
        return

    category_name = message.text
    
    if category_name in archive_cache:
        database.delete_content(category_name)
        
        # آپدیت متغیر سراسری
        archive_cache = database.get_all_content()
        
        bot.send_message(message.chat.id, f"🗑 دسته '{category_name}' حذف شد.")
    else:
        bot.send_message(message.chat.id, "❌ این دسته وجود ندارد.")
    
    show_admin_panel(message.chat.id)

# اجرای ربات
print("Bot is running with Admin Panel...")
bot.infinity_polling()
