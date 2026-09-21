import os
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import asyncio

TOKEN = os.environ.get("BOT_TOKEN")

entradas = {}
comidas = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot Activo ✅ /entrada /comida /fincomida /reporte")

async def entrada(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    hora = datetime.now().strftime("%H:%M")
    entradas[user] = hora
    await update.message.reply_text(f"Entrada {user} {hora} ✅")

async def comida(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    comidas[user] = datetime.now()
    await update.message.reply_text(f"Comida {user} 45 min 🍽️")
    await asyncio.sleep(2100)
    if user in comidas:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Quedan 10 min {user} ⏰")
    await asyncio.sleep(600)
    if user in comidas:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Se acabo {user} 🚨")
        del comidas[user]

async def fincomida(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    if user in comidas:
        del comidas[user]
        await update.message.reply_text(f"Fin comida {user} ✅")
    else:
        await update.message.reply_text("No estabas en comida")

async def reporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = "REPORTE GOVA\n"
    for u,h in entradas.items():
        texto += f"{u}: entrada {h}\n"
    await update.message.reply_text(texto if entradas else "Sin entradas")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("entrada", entrada))
app.add_handler(CommandHandler("comida", comida))
app.add_handler(CommandHandler("fincomida", fincomida))
app.add_handler(CommandHandler("reporte", reporte))
print("Bot prendido en Koyeb")
app.run_polling()
