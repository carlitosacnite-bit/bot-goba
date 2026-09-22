import asyncio
from datetime import datetime, timedelta
import json
import os
import time
import threading
from zoneinfo import ZoneInfo
from flask import Flask, jsonify
import pandas as pd
from telegram import ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

# Configuración de la zona horaria oficial para CDMX
TZ_CDMX = ZoneInfo("America/Mexico_City")

TOKEN = os.environ.get("BOT_TOKEN")
flask_app = Flask(__name__)

# ID de Administrador configurado exclusivamente para ti
ADMIN_ID = 734707763

# Archivo físico para persistencia de datos
DB_FILE = "registros_db.json"

# Referencia global para poder enviar mensajes desde Flask al bot de Telegram
bot_application = None


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


# 🔄 RUTA CLAVE: Este enlace es visitado por cron-job.org cada 5 minutos
@flask_app.route("/verificar-comidas")
def verificar_comidas_web():
  global bot_application
  if not bot_application:
    return jsonify({"status": "Bot no inicializado aún"}), 503

  registros = cargar_registros()
  ahora_ts = datetime.now(TZ_CDMX).timestamp()
  cambios_realizados = False
  alertas_enviadas_count = 0

  loop = asyncio.new_event_loop()
  asyncio.set_event_loop(loop)

  async def enviar_mensajes_pendientes():
    nonlocal cambios_realizados, alertas_enviadas_count
    for reg in registros:
      if reg.get("Accion") == "Comida Inicia":
        chat_id = reg.get("ChatId")
        nombre = reg.get("Paramedico")

        # 1. Alerta de 5 minutos antes (Minuto 45)
        if not reg.get("AlertaEnviada", False) and "TimestampFinAlerta" in reg:
          if ahora_ts >= reg["TimestampFinAlerta"]:
            reg["AlertaEnviada"] = True
            cambios_realizados = True
            alertas_enviadas_count += 1

            if chat_id:
              try:
                await bot_application.bot.send_message(
                    chat_id=chat_id,
                    text=(
                        f"⚠️ *¡Atención {nombre}!* Te quedan 5 minutos para que"
                        " termine tu tiempo de comida."
                    ),
                    parse_mode="Markdown",
                )
              except Exception as e:
                print(f"Error al enviar alerta previa de comida: {e}")

        # 2. Alerta de tiempo cumplido (Minuto 50)
        if not reg.get("AlertaFinEnviada", False) and "TimestampFinComida" in reg:
          if ahora_ts >= reg["TimestampFinComida"]:
            reg["AlertaFinEnviada"] = True
            cambios_realizados = True
            alertas_enviadas_count += 1

            if chat_id:
              try:
                await bot_application.bot.send_message(
                    chat_id=chat_id,
                    text=(
                        f"🚨 *¡Tiempo de comida finalizado, {nombre}!* "
                        "Tus pacientes esperan, a por ello."
                    ),
                    parse_mode="Markdown",
                )
              except Exception as e:
                print(f"Error al enviar alerta final de comida: {e}")

    if cambios_realizados:
      with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(registros, f, ensure_ascii=False, indent=4)

  loop.run_until_complete(enviar_mensajes_pendientes())
  return jsonify({
      "status": "OK",
      "alertas_enviadas": alertas_enviadas_count,
  }), 200


# Definición de los teclados dinámicos
TECLADO_INICIAL = [
    [KeyboardButton("🟢 Registrar Entrada")]
]

TECLADO_EN_TURNO = [
    [KeyboardButton("🔴 Registrar Salida"), KeyboardButton("🍽️ Iniciar Comida (50 min)")]
]

TECLADO_COMIDA = [
    [KeyboardButton("🔴 Registrar Salida")]
]


async def start(update, context):
  nombre = update.effective_user.first_name
  reply_markup = ReplyKeyboardMarkup(TECLADO_INICIAL, resize_keyboard=True)
  
  await update.message.reply_text(
      f"¡Bienvenido, {nombre}!\nInicia tu registro presionando el botón inferior:",
      reply_markup=reply_markup
  )


async def procesar_entrada(update, user_obj):
  ahora = datetime.now(TZ_CDMX)
  hora_str = ahora.strftime("%H:%M hrs del %d/%m/%Y")
  nombre = user_obj.first_name

  registro = {
      "Paramedico": nombre,
      "Accion": "Entrada",
      "FechaHora": hora_str,
  }
  guardar_registro_en_disco(registro)
  
  texto = f"✅ Entrada registrada para {nombre}: {hora_str}"
  reply_markup = ReplyKeyboardMarkup(TECLADO_EN_TURNO, resize_keyboard=True)
  await update.message.reply_text(texto, reply_markup=reply_markup)


async def procesar_salida(update, user_obj):
  ahora = datetime.now(TZ_CDMX)
  hora_str = ahora.strftime("%H:%M hrs del %d/%m/%Y")
  nombre = user_obj.first_name

  registro = {
      "Paramedico": nombre,
      "Accion": "Salida",
      "FechaHora": hora_str,
  }
  guardar_registro_en_disco(registro)
  
  texto = f"✅ Salida registrada para {nombre}: {hora_str}. ¡Buen descanso!"
  reply_markup = ReplyKeyboardMarkup(TECLADO_INICIAL, resize_keyboard=True)
  await update.message.reply_text(texto, reply_markup=reply_markup)


async def procesar_comida(update, user_obj):
  nombre = user_obj.first_name
  chat_id = update.effective_chat.id
  inicio_comida = datetime.now(TZ_CDMX)
  hora_inicio_str = inicio_comida.strftime("%H:%M hrs")
  hora_completa_str = inicio_comida.strftime("%H:%M hrs del %d/%m/%Y")

  timestamp_actual = inicio_comida.timestamp()

  registro = {
      "Paramedico": nombre,
      "Accion": "Comida Inicia",
      "FechaHora": hora_completa_str,
      "ChatId": chat_id,
      "TimestampFinAlerta": timestamp_actual + (45 * 60),  # Minuto 45 (Aviso previo)
      "TimestampFinComida": timestamp_actual + (50 * 60),  # Minuto 50 (Fin exacto)
      "AlertaEnviada": False,
      "AlertaFinEnviada": False,
  }
  guardar_registro_en_disco(registro)
  
  texto = (
      f"🍽️ ¡Buen provecho, {nombre}! Tu hora de comida inició a las"
      f" {hora_inicio_str}. Duración: 50 minutos. Te avisaré 5 minutos antes"
      " y al concluir tu tiempo."
  )
  reply_markup = ReplyKeyboardMarkup(TECLADO_COMIDA, resize_keyboard=True)
  await update.message.reply_text(texto, reply_markup=reply_markup)


# Handlers para comandos de texto tradicionales
async def entrada(update, context):
  await procesar_entrada(update, update.effective_user)

async def salida(update, context):
  await procesar_salida(update, update.effective_user)

async def comida(update, context):
  await procesar_comida(update, update.effective_user)


# Manejador para los clics en los botones fijos inferiores dinámicos
async def manejar_botones_texto(update, context):
  texto = update.message.text
  user = update.effective_user

  if texto == "🟢 Registrar Entrada":
    await procesar_entrada(update, user)
  elif texto == "🔴 Registrar Salida":
    await procesar_salida(update, user)
  elif texto == "🍽️ Iniciar Comida (50 min)":
    await procesar_comida(update, user)


async def excel_stats(update, context):
  user_id = update.effective_user.id

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
  global bot_application
  time.sleep(3)  # Pausa de seguridad para evitar conflicto de instancias

  loop = asyncio.new_event_loop()
  asyncio.set_event_loop(loop)

  async def init_and_run():
    global bot_application
    bot_application = ApplicationBuilder().token(TOKEN).build()
    
    # Comandos
    bot_application.add_handler(CommandHandler("start", start))
    bot_application.add_handler(CommandHandler("entrada", entrada))
    bot_application.add_handler(CommandHandler("salida", salida))
    bot_application.add_handler(CommandHandler("comida", comida))
    bot_application.add_handler(CommandHandler("excel", excel_stats))
    
    # Manejador de texto para los botones fijos inferiores
    bot_application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_botones_texto))

    await bot_application.bot.delete_webhook(drop_pending_updates=True)

    await bot_application.initialize()
    await bot_application.start()
    await bot_application.updater.start_polling(drop_pending_updates=True)

  try:
    loop.run_until_complete(init_and_run())
    loop.run_forever()
  except Exception as e:
    print(f"Error en el hilo del bot: {e}")


threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
  flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
