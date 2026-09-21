import asyncio
from datetime import datetime, timedelta
import json
import os
import threading
from zoneinfo import ZoneInfo
from flask import Flask, send_file
import pandas as pd
from telegram.ext import ApplicationBuilder, CommandHandler

# Configuración de la zona horaria oficial para CDMX
TZ_CDMX = ZoneInfo("America/Mexico_City")

TOKEN = os.environ.get("BOT_TOKEN")
flask_app = Flask(__name__)

# ID de Administrador configurado exclusivamente para ti
ADMIN_ID = 734707763

# Archivo físico para persistencia de datos (evita pérdida al dormir el servidor)
DB_FILE = "registros_db.json"


def cargar_registros():
  if os.path.exists(DB_FILE):
    try:
      with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
    except Exception:
      return []
  return []


def guardar_registro_en_disco(nuevo_registro):
  registros = cargar_registros()
  registros.append(nuevo_registro)
  with open(DB_FILE, "w", encoding="utf-8") as f:
    json.dump(registros, f, ensure_ascii=False, indent=4)


@flask_app.route("/")
def home():
  return "Bot CDMX & Paramedicos OK - Operativo"


async def entrada(update, context):
  ahora = datetime.now(TZ_CDMX)
  hora_str = ahora.strftime("%H:%M hrs del %d/%m/%Y")
  nombre = update.effective_user.first_name

  registro = {
      "Paramedico": nombre,
      "Accion": "Entrada",
      "FechaHora": hora_str,
  }
  guardar_registro_en_disco(registro)

  await update.message.reply_text(f"✅ Entrada registrada para {nombre}: {hora_str}")


async def salida(update, context):
  ahora = datetime.now(TZ_CDMX)
  hora_str = ahora.strftime("%H:%M hrs del %d/%m/%Y")
  nombre = update.effective_user.first_name

  registro = {
      "Paramedico": nombre,
      "Accion": "Salida",
      "FechaHora": hora_str,
  }
  guardar_registro_en_disco(registro)

  await update.message.reply_text(f"✅ Salida registrada para {nombre}: {hora_str}")


async def tarea_alerta_comida(context, chat_id, nombre):
  # Esperar 45 minutos (45 * 60 segundos) en segundo plano de forma segura
  await asyncio.sleep(45 * 60)
  await context.bot.send_message(
      chat_id=chat_id,
      text=(
          f"⚠️ *¡Atención {nombre}!* Te quedan 5 minutos para que termine tu"
          " tiempo de comida."
      ),
      parse_mode="Markdown",
  )


async def comida(update, context):
  nombre = update.effective_user.first_name
  chat_id = update.effective_chat.id
  inicio_comida = datetime.now(TZ_CDMX)
  hora_inicio_str = inicio_comida.strftime("%H:%M hrs")
  hora_completa_str = inicio_comida.strftime("%H:%M hrs del %d/%m/%Y")

  registro = {
      "Paramedico": nombre,
      "Accion": "Comida Inicia",
      "FechaHora": hora_completa_str,
  }
  guardar_registro_en_disco(registro)

  await update.message.reply_text(
      f"🍽️ ¡Buen provecho, {nombre}! Tu hora de comida inició a las"
      f" {hora_inicio_str}. Duración: 50 minutos. Te avisaré 5 minutos antes"
      " de que termine."
  )

  # Programar la alerta de forma asíncrona sin librerías externas
  asyncio.create_task(tarea_alerta_comida(context, chat_id, nombre))


async def excel_stats(update, context):
  user_id = update.effective_user.id

  # 🔒 SEGURIDAD: Verifica que sea exactamente tu ID de administrador
  if user_id != ADMIN_ID:
    await update.message.reply_text(
        "⛔ No tienes permisos para solicitar el archivo de estadísticas."
        " Comando exclusivo del administrador."
    )
    return

  registros_operativos = cargar_registros()

  if not registros_operativos:
    await update.message.reply_text(
        "📂 Aún no hay registros guardados en el sistema."
    )
    return

  df = pd.DataFrame(registros_operativos)
  archivo_path = "estadisticas_paramedicos.xlsx"
  df.to_excel(archivo_path, index=False, engine="openpyxl")

  await update.message.reply_document(
      document=open(archivo_path, "rb"),
      filename="Estadisticas_Paramedicos.xlsx",
      caption=(
          "📊 Reporte de estadísticas autorizado solicitado por el"
          " administrador."
      ),
  )


def run_bot():
  loop = asyncio.new_event_loop()
  asyncio.set_event_loop(loop)

  async def start():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("entrada", entrada))
    app.add_handler(CommandHandler("salida", salida))
    app.add_handler(CommandHandler("comida", comida))
    app.add_handler(CommandHandler("excel", excel_stats))
    await app.bot.delete_webhook(drop_pending_updates=True)

    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)

  try:
    loop.run_until_complete(start())
    loop.run_forever()
  except Exception as e:
    print(f"Error en el hilo del bot: {e}")


threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
  flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
