import os
from datetime import datetime, timedelta

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ───────────────── CONFIG ─────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN")  # ← RENDER USA ESTO

ADMIN_GROUP_ID = -1003517104846
GROUP_LINK = "https://t.me/+bzEP-l8AmJZhMzgx"

PLANS = {
    "5":  ("5 días", 10, "https://www.roblox.com/es/game-pass/1603749316"),
    "10": ("10 días", 15, "https://www.roblox.com/es/game-pass/1585903887"),
    "15": ("15 días", 25, "https://www.roblox.com/es/game-pass/1586158340"),
    "30": ("30 días", 40, "https://www.roblox.com/es/game-pass/1576771845/CUPO-30-D-AS"),
    "40": ("40 días", 50, "https://www.roblox.com/es/game-pass/1583798828"),
    "60": ("60 días", 70, "https://www.roblox.com/es/game-pass/1604115224"),
    "90": ("90 días", 100, "https://www.roblox.com/es/game-pass/1605063357"),
}

# ───────────────── ESTADO ─────────────────
users = {}
history = {}
pending_photos = {}
pending_type = {}

# ───────────────── TECLADOS ───────────────
def plan_buttons(prefix):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{v[0]} - {v[1]} robuxs", callback_data=f"{prefix}_{k}")]
        for k, v in PLANS.items()
    ])

def admin_buttons(uid, stage):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Aprobar", callback_data=f"approve_{stage}_{uid}"),
            InlineKeyboardButton("❌ Rechazar", callback_data=f"reject_{stage}_{uid}")
        ]
    ])

# ───────────────── START ──────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "(๑˃‌ᴗ˂‌)-- ¡holi! bienvenido a cherry's shopping, adquiere de manera rápida y segura.\n\n"
        "⪧ /buy\n⪧ /renew\n⪧ /sub\n\n"
        "Pulsa el botón para iniciar tu compra ⇣",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("buy", callback_data="buy_start")]
        ])
    )

# ───────────────── BUY / RENEW ────────────
async def buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data in ("buy_start", "buy"):
        await q.edit_message_text(
            "⌗   Por favor, selecciona uno de los planes a continuación:",
            reply_markup=plan_buttons("buy")
        )
        return

    if q.data.startswith(("buy_", "renew_")):
        mode, plan_id = q.data.split("_")
        plan = PLANS[plan_id]

        users[q.from_user.id] = {"plan": plan_id}
        pending_type[q.from_user.id] = mode

        await q.edit_message_text(
            "⌗   ¡Gracias! un administrador revisará tu solicitud."
        )

        await context.bot.send_message(
            chat_id=ADMIN_GROUP_ID,
            text=(
                f"🛒 NUEVA SOLICITUD ({mode.upper()})\n\n"
                f"👤 @{q.from_user.username or q.from_user.id}\n"
                f"📦 {plan[0]} - {plan[1]} robux"
            ),
            reply_markup=admin_buttons(q.from_user.id, "req")
        )

# ───────────────── ADMIN ──────────────────
async def admin_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    action, stage, uid = q.data.split("_")
    uid = int(uid)

    if uid not in users:
        return

    plan_id = users[uid]["plan"]
    plan = PLANS[plan_id]

    if stage == "req" and action == "approve":
        pending_photos[uid] = True
        await context.bot.send_message(
            chat_id=uid,
            text=f"🔗 {plan[2]}\n\nEnvía la captura del pago."
        )

    elif stage == "pay" and action == "approve":
        end = datetime.now() + timedelta(days=int(plan_id))
        pending_photos.pop(uid, None)

        await context.bot.send_message(
            chat_id=uid,
            text=(
                "⌗   ¡Compra / Renovación Exitosa! 🎊\n\n"
                f"Tu plan vence el {end.strftime('%d/%m/%Y')}.\n\n"
                f"🔗 {GROUP_LINK}"
            )
        )

# ───────────────── FOTO ───────────────────
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    if uid not in pending_photos:
        return

    await context.bot.send_photo(
        chat_id=ADMIN_GROUP_ID,
        photo=update.message.photo[-1].file_id,
        caption=f"📸 @{update.message.from_user.username or uid}",
        reply_markup=admin_buttons(uid, "pay")
    )

# ───────────────── MAIN ───────────────────
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(buy_callback, pattern="^(buy|renew)"))
app.add_handler(CallbackQueryHandler(admin_request, pattern="^(approve|reject)"))
app.add_handler(MessageHandler(filters.PHOTO, photo_handler))

print("🤖 Cherry’s bot activo en Render")
app.run_polling()
