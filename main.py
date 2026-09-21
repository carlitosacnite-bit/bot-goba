import os, json, threading, asyncio
from datetime import datetime, timedelta
from flask import Flask
from telegram.ext import ApplicationBuilder, CommandHandler

TOKEN = os.environ.get("BOT_TOKEN")
ARCHIVO = "entradas.json"
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot GOVA CDMX Activo - 20:xx"

def cargar():
    if os.path.exists(ARCHIVO):
        try:
            with open(ARCHIVO, "r") as f: return json.load(f)
        except: return {}
    return {}
def guardar(data):
    with open(ARCHIVO, "w") as f: json.dump(data, f)

async def entrada(update, context):
    ahora = datetime.utcnow() - timedelta(hours=6)
    hora = ahora.strftime("%H:%M hrs del %d/%m/%Y")
    uid = str(update.effective_user.id)
    data = cargar(); data[uid] = hora; guardar(data)
    await update.message.reply_text(f"✅ Entrada CDMX registrada: {hora}")

async def salida(update, context):
    ahora = datetime.utcnow() - timedelta(hours=6)
    hora = ahora.strftime("%H:%M hrs del %d/%m/%Y")
    uid = str(update.effective_user.id)
    data = cargar()
    ent = data.get(uid, "sin registro")
    if uid in data: del data[uid]; guardar(data)
    await update.message.reply_text(f"✅ Salida: {hora}\nEntrada fue: {ent}")

def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("entrada", entrada))
    app.add_handler(CommandHandler("salida", salida))
    app.run_polling()

threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
