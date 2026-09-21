import os, json, threading
from datetime import datetime, timedelta
from flask import Flask
from telegram.ext import ApplicationBuilder, CommandHandler

TOKEN = os.environ.get("BOT_TOKEN")
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot Activo"

async def entrada(update, context):
    ahora = datetime.utcnow() - timedelta(hours=6)
    hora = ahora.strftime("%H:%M hrs del %d/%m/%Y")
    await update.message.reply_text(f"Entrada: {hora}")

async def salida(update, context):
    ahora = datetime.utcnow() - timedelta(hours=6)
    hora = ahora.strftime("%H:%M hrs del %d/%m/%Y")
    await update.message.reply_text(f"Salida: {hora}")

def run_bot():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("entrada", entrada))
    app.add_handler(CommandHandler("salida", salida))
    app.run_polling(stop_signals=None)

threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
