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

  # ⚠️ CORRECCIÓN AQUÍ: Usar TZ_CDMX para evitar conflictos en el temporizador
  tiempo_alerta = datetime.now(TZ_CDMX) + timedelta(minutes=45)

  scheduler.add_job(
      enviar_alerta_comida_termina,
      "date",
      run_date=tiempo_alerta,
      args=[context, chat_id, nombre],
  )
