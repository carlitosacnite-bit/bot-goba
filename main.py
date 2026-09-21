import asyncio
from datetime import datetime
import os
import threading
from zoneinfo import ZoneInfo
from flask import Flask
from telegram.ext import ApplicationBuilder, CommandHandler

# Configuración de la zona horaria oficial para CDMX
TZ_CDMX = ZoneInfo("America/Mexico_City")

TOKEN = os.environ.get("BOT_TOKEN")
flask_app = Flask(__name__)


@flask_app.route("/")
def home():
  return "Bot CDMX OK - Operativo"


async def entrada(update, context):
  ahora = datetime.now(TZ_CDMX)
  hora = ahora.strftime("%H:%M hrs del %d/%m/%Y")
  await update.message.reply_text(f"✅ Entrada registrada: {hora}")


async def salida(update, context):
  ahora = datetime.now(TZ_CDMX)
  hora = ahora.strftime("%H:%M hrs del %d/%m/%Y")
  await update.message.reply_text(f"✅ Salida registrada: {hora}")


def run_bot():
  # Creamos un nuevo bucle de eventos limpio para el hilo
  loop = asyncio.new_event_loop()
  asyncio.set_event_loop(loop)

  async def start():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("entrada", entrada))
    app.add_handler(CommandHandler("salida", salida))
    await app.bot.delete_webhook(drop_pending_updates=True)

    # Inicializamos y arrancamos el bot de manera compatible con hilos
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)

  try:
    loop.run_until_complete(start())
    # Mantenemos el bucle vivo
    loop.run_forever()
  except Exception as e:
    print(f"Error en el hilo del bot: {e}")


# Lanzar el bot en segundo plano junto con Flask
threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
  flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
