import os
import threading
from datetime import datetime
from flask import Flask
from telegram.ext import ApplicationBuilder, CommandHandler
import asyncio

TOKEN = os.environ.get("BOT_TOKEN")
flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return "Bot GOVA 24/7 Activo"

entradas = {}
comidas = {}

async def start(update, context):
    await update.message.reply_text("Bot Activo /entrada /comida /fincomida /reporte")
async def entrada(update, context):
    user = update.effective_user.first_name
    hora = datetime.now().strftime("%H:%M")
    entradas[user] = hora
    await update.message.reply_text(f"Entrada {user} {hora}")
async def comida(update, context):
    user = update.effective_user.first_name
    comidas[user] = True
    await update.message.reply_text(f"Comida {user} 45 min")
    await asyncio.sleep(2100)
    if user in comidas:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Quedan 10 min {user}")
    await asyncio.sleep(600)
    if user in comidas:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Se acabo {user}")
        del comidas[user]
async def fincomida(update, context):
    user = update.effective_user.first_name
    if user in comidas:
        del comidas[user]
        await update.message.reply_text(f"Fin comida {user}")
    else:
        await update.message.reply_text("No estabas en comida")
async def reporte(update, context):
    texto = "REPORTE GOVA\n"
    for u,h in entradas.items():
        texto += f"{u}: entrada {h}\n"
    await update.message.reply_text(texto if entradas else "Sin entradas")

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
