import os
import json
import threading
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Flask
from telegram.ext import ApplicationBuilder, CommandHandler

TOKEN = os.environ.get("BOT_TOKEN")
ZONA_MEXICO = ZoneInfo("America/Mexico_City")

flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return "Bot GOVA 24/7 Activo - Hora CDMX"

# --- GUARDADO PERMANENTE ---
ARCHIVO_ENTRADAS = "entradas.json"

def cargar_entradas():
    if os.path.exists(ARCHIVO_ENTRADAS):
        try:
            with open(ARCHIVO_ENTRADAS, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def guardar_entradas():
    with open(ARCHIVO_ENTRADAS, "w") as f:
        json.dump(entradas, f)

entradas = cargar_entradas()
comidas = {}

def hora_mexico():
    return datetime.now(ZONA_MEXICO).strftime("%H:%M")

def fecha_mexico():
    return datetime.now(ZONA_MEXICO).strftime("%d/%m/%Y")

async def start(update, context):
    await update.message.reply_text("Bot GOVA Activo 24/7\n/entrada /comida /fincomida /reporte")

async def entrada(update, context):
    user = update.effective_user.first_name
    hora = hora_mexico()
    fecha = fecha_mexico()
    # Guardamos con fecha
    entradas[user] = f"{fecha} {hora}"
    guardar_entradas()
    await update.message.reply_text(f"✅ Entrada {user} {hora} hrs")

async def comida(update, context):
    user = update.effective_user.first_name
    comidas[user] = True
    await update.message.reply_text(f"🍽️ Comida {user} 18:56 -> 45 min (hasta las {(datetime.now(ZONA_MEXICO).astimezone(ZONA_MEXICO).replace() )})")
    # Mensaje simple
    await update.message.reply_text(f"🍽️ Comida {user} 45 min - Hora: {hora_mexico()}")
    await asyncio.sleep(35*60) # 35 min
    if user in comidas:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"⏰ Quedan 10 min {user}")
    await asyncio.sleep(10*60) # 10 min mas = 45
    if user in comidas:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"🚨 Se acabó el tiempo de comida {user}!")
        del comidas[user]

async def fincomida(update, context):
    user = update.effective_user.first_name
    if user in comidas:
        del comidas[user]
        await update.message.reply_text(f"✅ Fin comida {user} {hora_mexico()}")
    else:
        await update.message.reply_text("No estabas en comida")

async def reporte(update, context):
    if not entradas:
        await update.message.reply_text("Sin entradas hoy")
        return
    texto = f"📋 REPORTE GOVA - {fecha_mexico()}\n\n"
    for u, fh in entradas.items():
        texto += f"• {u}: {fh}\n"
    texto += f"\nEn comida ahora: {', '.join(comidas.keys()) if comidas else 'Nadie'}"
    await update.message.reply_text(texto)

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
