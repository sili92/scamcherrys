import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
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
BOT_TOKEN = os.getenv("BOT_TOKEN")

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

# ───────────────── WEB SERVER (RENDER) ────
def run_web():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Cherry's bot running")

    server = HTTPServer(("0.0.0.0", 10000), Handler)
    server.serve_forever()

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
        "﹟  Te presentamos nuestros comandos:\n\n"
        "⪧ /buy\n⪧ /renew\n⪧ /sub\n⪧ /contact\n⪧ /channels\n"
        "⪧ /historial\n⪧ /refes\n⪧ /othermethods\n\n"
        "─┈   pulsa el botón para iniciar tu compra ⇣",
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
            "⌗   ¡Gracias! un administrador se encargará de revisar tu solicitud y en breve se te notificarán novedades."
        )

        await context.bot.send_message(
            chat_id=ADMIN_GROUP_ID,
            text=(
                f"🛒 NUEVA SOLICITUD ({mode.upper()})\n\n"
                f"👤 Usuario: @{q.from_user.username or q.from_user.id}\n"
                f"📦 Plan: {plan[0]} - {plan[1]} robux"
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

    if stage == "req":
        if action == "approve":
            pending_photos[uid] = True
            await context.bot.send_message(
                chat_id=uid,
                text=(
                    "⌗   ¡Tu solicitud fué aprobada!\n"
                    "Te indicamos cómo proseguir con tu compra.\n\n"
                    f"🔗 {plan[2]}\n\n"
                    "⪧ Compra el gamepass y envía la captura sin modificar."
                )
            )
        else:
            await context.bot.send_message(
                chat_id=uid,
                text="⌗   Tu solicitud fue rechazada."
            )

    elif stage == "pay":
        if action == "approve":
            end = datetime.now() + timedelta(days=int(plan_id))

            history.setdefault(uid, []).append({
                "plan": plan,
                "end": end,
                "renewed": pending_type.get(uid) == "renew"
            })

            users[uid]["expires"] = end
            pending_photos.pop(uid, None)

            header = (
                "⌗   ¡Renovación Exitosa! 🎊\n\n"
                if pending_type.get(uid) == "renew"
                else "⌗   ¡Compra Exitosa! 🎊\n\n"
            )

            await context.bot.send_message(
                chat_id=uid,
                text=(
                    header +
                    f"Tu plan de {plan[0]} {plan[1]} robux empieza ahora y vence el "
                    f"{end.strftime('%d/%m/%Y')}. "
                    "Muchísimas gracias por confiar en Cherry's Priv. 💕\n\n"
                    f"🔗 {GROUP_LINK}"
                )
            )
        else:
            await context.bot.send_message(
                chat_id=uid,
                text=(
                    "⌗  ⁉️  Tuvimos problemas al validar tu comprobante.\n\n"
                    "— NO recortes la foto\n"
                    "— NO tapes nada\n"
                    "— Adjunta tu usuario de Roblox\n\n"
                    "Vuelve a enviar la foto."
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
        caption=f"📸 COMPROBANTE\n👤 @{update.message.from_user.username or uid}",
        reply_markup=admin_buttons(uid, "pay")
    )

# ───────────────── COMANDOS ───────────────
async def renew(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⌗ Has solicitado la renovación de tu plan, por favor pulsa el botón de tu preferencia.",
        reply_markup=plan_buttons("renew")
    )

async def sub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    if uid in users and "expires" in users[uid]:
        plan = PLANS[users[uid]["plan"]]
        await update.message.reply_text(
            f"⌗   ¡Hola! Esta es tu suscripción actual:\n\n"
            f"{plan[0]} {plan[1]} robux\n"
            f"Vence en {users[uid]['expires'].strftime('%d/%m/%Y')}"
        )
    else:
        await update.message.reply_text("⌗   No tienes una suscripción activa.")

async def historial_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    if uid not in history:
        await update.message.reply_text(
            "⌗   No has adquirido Cherry's priv antes. ¿Qué esperas para probarlo?"
        )
        return

    text = "⌗   Anteriormente adquiriste estos planes:\n\n"
    for h in history[uid]:
        text += (
            f"{h['plan'][0]} {h['plan'][1]} robux "
            f"venció el {h['end'].strftime('%d/%m/%Y')} "
            f"{'renovado' if h['renewed'] else 'no renovado'}\n"
        )
    await update.message.reply_text(text)

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⌗   Puedes contactar a estos usuarios:\n\n"
        "Owner — @venustelar\n"
        "Owner — @zilbato\n"
        "Co-owner — @kirschteiinz"
    )

async def channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⌗   Estos son nuestros canales:\n\n"
        "࿔ Referencias: https://t.me/+FmV2e23GHJA3NjE0\n"
        "࿔ Información: https://t.me/infocherrys"
    )

async def othermethods(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⌗   Estos son nuestros métodos de pago:\n\n"
        "꩜ @zilbato 🇪🇸🇪🇺 → paypal, bizum & robuxs\n"
        "꩜ @heavenkoop 🇲🇽 → paypal, oxxo, cashi, transferencia\n"
        "꩜ @rougtoile 🇵🇪 → paypal, yape, plin\n"
        "꩜ @venustelar 🇨🇱 → transferencia CLP\n"
        "꩜ @kirschteiinz 🇻🇪 → transferencia y pago móvil"
    )

# ───────────────── MAIN ───────────────────
if __name__ == "__main__":
    print("🤖 Cherry’s bot activo")

    threading.Thread(target=run_web, daemon=True).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("renew", renew))
    app.add_handler(CommandHandler("sub", sub))
    app.add_handler(CommandHandler("historial", historial_cmd))
    app.add_handler(CommandHandler("contact", contact))
    app.add_handler(CommandHandler("channels", channels))
    app.add_handler(CommandHandler("othermethods", othermethods))

    app.add_handler(CallbackQueryHandler(buy_callback, pattern="^(buy|renew)"))
    app.add_handler(CallbackQueryHandler(admin_request, pattern="^(approve|reject)"))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))

    app.run_polling()
