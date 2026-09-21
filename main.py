import os, json, threading, asyncio
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Flask
from telegram.ext import ApplicationBuilder, CommandHandler

TOKEN = os.environ.get("BOT_TOKEN")
ZONA = ZoneInfo("America/Mexico_City")

flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return "Bot GOVA CDMX Activo"

ARCHIVO = "entradas.json"

def cargar():
    if os.path.exists(ARCHIVO):
        try:
            with open(ARCHIVO, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def guardar(data):
    with open(ARCHIVO, "w") as f:
        json.dump(data, f)

entradas = cargar()
comidas = {}

def ahora():
    return datetime.now(ZONA).strftime("%H:%M")

def hoy():
    return datetime.now(ZONA).strftime("%d/%m/%Y")

async def start(update, context):
    await update.message.reply_text("Bot GOVA CDMX\n/entrada /comida /fincomida /reporte")

async def entrada(update, context):
    user = update.effective_user.first_name
    entradas[user] = f"{hoy()} {ahora()}"
    guardar(entradas)
    await update.message.reply_text(f"✅ Entrada {user} {ahora()} hrs")

async def comida(update, context):
    user = update.effective_user.first_name
    comidas[user] = True
    await update.message.reply_text(f"🍽️ Comida {user} 45 min - {ahora()} hrs")
    await asyncio.sleep(35*60)
    if user in comidas:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"⏰ Quedan 10 min {user}")
    await asyncio.sleep(10*60)
    if user in comidas:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"🚨 Se acabó {user}!")
        del comidas[user]

async def fincomida(update, context):
    user = update.effective_user.first_name
    if user in comidas:
        del comidas[user]
        await update.message.reply_text(f"✅ Fin comida {user} {ahora()}")
    else:
        await update.message.reply_text("No estabas en comida")

async def reporte(update, context):
    if not entradas:
        await update.message.reply_text("Sin entradas")
        return
    txt = f"📋 REPORTE GOVA - {hoy()}\n\n"
    for u, fh in entradas.items():
        txt += f"• {u}: {fh}\n"
    if comidas:
        txt += f"\nEn comida: {', '.join(comidas.keys())}"
    await update.message.reply_text(txt)

def run_bot():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("entrada", entrada))
    app.add_handler(CommandHandler("comida", comida))
    app.add_handler(CommandHandler("fincomida", fincomida))
    app.add_handler(CommandHandler("reporte", reporte))
    app.run_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host='0.0.0.0', port=port)
