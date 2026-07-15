from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, ContextTypes, filters
)

TOKEN = "8911738747:AAHKSuiMeGXSJXCsz0GU5ZaBb_u2Wo3ypZ4"
ADMIN_ID = 6506763272

PHONE, NAME, ADDRESS = range(3)

# محصولات
products = {
    "tshirt": {"name": "👕 تی‌شرت", "price": 200000},
    "pants": {"name": "👖 شلوار", "price": 400000},
    "bag": {"name": "👜 کیف", "price": 300000},
}

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🛍 محصولات", callback_data="products")],
        [InlineKeyboardButton("📞 تماس با ما", callback_data="contact")],
        [InlineKeyboardButton("ℹ️ درباره ما", callback_data="about")],
    ]
    await update.message.reply_text(
        "👋 خوش اومدی به فروشگاه ما",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------- محصولات ----------------
async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = []
    for key, item in products.items():
        keyboard.append([InlineKeyboardButton(item["name"], callback_data=key)])

    keyboard.append([InlineKeyboardButton("🛒 سبد خرید", callback_data="cart")])

    await query.message.reply_text(
        "🛍 محصولات:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------- جزئیات محصول ----------------
async def product_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    product = products[query.data]

    keyboard = [
        [InlineKeyboardButton("➕ افزودن به سبد", callback_data="add_" + query.data)],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="products")]
    ]

    await query.message.reply_text(
        f"{product['name']}\n💰 {product['price']} تومان",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------- افزودن به سبد ----------------
async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    product_id = query.data.replace("add_", "")

    cart = context.user_data.get("cart", [])
    cart.append(product_id)
    context.user_data["cart"] = cart

    keyboard = [
        [InlineKeyboardButton("🛒 سبد خرید", callback_data="cart")],
        [InlineKeyboardButton("🛍 ادامه خرید", callback_data="products")]
    ]

    await query.message.reply_text(
        "✅ اضافه شد به سبد",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------- سبد خرید ----------------
async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    cart = context.user_data.get("cart", [])

    if not cart:
        await query.message.reply_text("سبد خالیه 😅")
        return

    text = "🛒 سبد خرید:\n\n"
    total = 0

    for item in cart:
        p = products[item]
        text += f"{p['name']} - {p['price']} تومان\n"
        total += p["price"]

    text += f"\n💰 مجموع: {total}"

    keyboard = [
        [InlineKeyboardButton("✅ تکمیل خرید", callback_data="checkout")],
        [InlineKeyboardButton("🛍 ادامه خرید", callback_data="products")]
    ]

    await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# ---------------- شروع سفارش ----------------
async def checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    btn = KeyboardButton("📱 ارسال شماره", request_contact=True)
    keyboard = ReplyKeyboardMarkup([[btn]], resize_keyboard=True)

    await query.message.reply_text(
        "شماره‌تو بفرست:",
        reply_markup=keyboard
    )

    return PHONE

# ---------------- شماره ----------------
async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        context.user_data["phone"] = update.message.contact.phone_number
    else:
        context.user_data["phone"] = update.message.text

    await update.message.reply_text(
        "نامتو بفرست:",
        reply_markup=ReplyKeyboardRemove()
    )
    return NAME

# ---------------- نام ----------------
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("آدرسو بفرست:")
    return ADDRESS

# ---------------- آدرس ----------------
async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["address"] = update.message.text

    cart = context.user_data.get("cart", [])
    total = 0
    text = "🛒 سفارش جدید:\n\n"

    for item in cart:
        p = products[item]
        text += f"{p['name']} - {p['price']}\n"
        total += p["price"]

    text += f"\n👤 {context.user_data['name']}"
    text += f"\n📱 {context.user_data['phone']}"
    text += f"\n📍 {context.user_data['address']}"
    text += f"\n💰 {total}"

    await context.bot.send_message(chat_id=ADMIN_ID, text=text)

    await update.message.reply_text("✅ سفارش ثبت شد")

    context.user_data.clear()
    return ConversationHandler.END

# ---------------- سایر ----------------
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text("ما یه فروشگاه خفنیم 😎")

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text("📞 09123456789")

# ---------------- اجرا ----------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(checkout, pattern="^checkout$")],
        states={
            PHONE: [MessageHandler(filters.ALL, get_phone)],
            NAME: [MessageHandler(filters.TEXT, get_name)],
            ADDRESS: [MessageHandler(filters.TEXT, get_address)],
        },
        fallbacks=[]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(show_products, pattern="^products$"))
    app.add_handler(CallbackQueryHandler(contact, pattern="^contact$"))
    app.add_handler(CallbackQueryHandler(about, pattern="^about$"))
    app.add_handler(CallbackQueryHandler(add_to_cart, pattern="^add_"))
    app.add_handler(CallbackQueryHandler(show_cart, pattern="^cart$"))
    app.add_handler(CallbackQueryHandler(product_detail, pattern="^(tshirt|pants|bag)$"))
    app.add_handler(conv)

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()