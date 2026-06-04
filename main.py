import aiohttp
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from io import BytesIO
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)
from urllib.parse import urljoin

# --- Estados del ConversationHandler ---
PEDIR_ANIO, PEDIR_UNIDAD, PEDIR_NUM, MOSTRAR_CAPTCHA, PEDIR_CAPTCHA, CONSULTA_FINAL = range(6)

# --- VALIDACIONES ---
def validar_anio(anio_text):
    try:
        anio = int(anio_text)
        if 2020 <= anio <= datetime.now().year:
            return True, anio
        return False, None
    except ValueError:
        return False, None

def validar_unidad(unidad_text):
    return unidad_text.isdigit() and len(unidad_text) <= 6

def validar_numero(numero_text):
    return numero_text.isdigit() and len(numero_text) <= 10


# --- INICIO ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"🚀 Usuario @{update.effective_user.username or update.effective_user.id} inició el bot.")
    keyboard = [["/consulta_exp", "/consulta_cert"]]
    await update.message.reply_text(
        "👋 ¡Bienvenido! Elige el tipo de consulta:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    )


# --- CANCELAR ---
async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = context.user_data.get("session")
    if session and not session.closed:
        await session.close()

    context.user_data.clear()
    await update.message.reply_text("❌ Consulta cancelada correctamente.")

    # Mostrar menú principal nuevamente
    keyboard = [["/consulta_exp", "/consulta_cert"]]
    await update.message.reply_text(
        "📋 Elija una nueva acción:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    )

    print(f"🧹 Usuario @{update.effective_user.username or update.effective_user.id} canceló y volvió al menú.")
    return ConversationHandler.END




# --- CONSULTA EXPEDIENTE ---
async def consulta_exp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['tipo'] = 'expediente'
    await update.message.reply_text("Ingrese el año de ejecución (2020 - actual):")
    return PEDIR_ANIO


# --- CONSULTA CERTIFICADO ---
async def consulta_cert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['tipo'] = 'certificado'
    await update.message.reply_text("Ingrese el año del certificado (2020 - actual):")
    return PEDIR_ANIO


# --- PEDIR AÑO ---
async def pedir_unidad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    anio_text = update.message.text.strip()
    valido, anio = validar_anio(anio_text)
    if not valido:
        await update.message.reply_text(f"Año inválido. Ingrese un año entre 2020 y {datetime.now().year}:")
        return PEDIR_ANIO
    context.user_data['anio'] = anio
    await update.message.reply_text("Ingrese el código de la unidad ejecutora:")
    return PEDIR_UNIDAD


# --- PEDIR UNIDAD ---
async def pedir_numero(update: Update, context: ContextTypes.DEFAULT_TYPE):
    unidad = update.message.text.strip()
    if not validar_unidad(unidad):
        await update.message.reply_text("Código inválido. Debe ser numérico y hasta 6 dígitos:")
        return PEDIR_UNIDAD
    context.user_data['unidad'] = unidad
    await update.message.reply_text("Ingrese el número de expediente/certificado:")
    return PEDIR_NUM


# --- MOSTRAR CAPTCHA ---
async def mostrar_captcha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    numero = update.message.text.strip()
    if not validar_numero(numero):
        await update.message.reply_text("Número inválido. Debe ser numérico y hasta 10 dígitos:")
        return PEDIR_NUM

    context.user_data['numero'] = numero
    tipo = context.user_data['tipo']
    url_base = (
        "https://apps2.mef.gob.pe/consulta-vfp-webapp/consultaExpediente.jspx"
        if tipo == "expediente"
        else "https://apps2.mef.gob.pe/consulta-vfp-webapp/consultaCertificado.jspx"
    )

    # Crear sesión persistente con headers reales
    session = aiohttp.ClientSession(headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": url_base,
    })
    context.user_data['session'] = session

    async with session.get(url_base) as resp:
        html = await resp.text()
        soup = BeautifulSoup(html, "html.parser")
        captcha_tag = soup.find("img", id="captchaImage")

        if not captcha_tag:
            await update.message.reply_text("⚠️ No se pudo obtener captcha. Intente nuevamente.")
            await session.close()
            return ConversationHandler.END

        captcha_src = captcha_tag["src"]
        captcha_url = urljoin(url_base, captcha_src)
        async with session.get(captcha_url) as img_resp:
            img_bytes = await img_resp.read()
            await update.message.reply_photo(img_bytes, caption="🔢 Ingrese el texto del captcha:")

    print(f"🧩 Captcha enviado a @{update.effective_user.username or update.effective_user.id}")
    return PEDIR_CAPTCHA


# --- PROCESAR CONSULTA ---
async def procesar_consulta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    captcha = update.message.text.strip()

    if not all(k in context.user_data for k in ["anio", "unidad", "numero", "tipo", "session"]):
        await update.message.reply_text("⚠️ Sesión expirada. Usa /start para reiniciar.")
        return ConversationHandler.END

    anio = context.user_data["anio"]
    unidad = context.user_data["unidad"]
    numero = context.user_data["numero"]
    tipo = context.user_data["tipo"]
    session = context.user_data["session"]

    url_post = (
        "https://apps2.mef.gob.pe/consulta-vfp-webapp/actionConsultaExpediente.jspx"
        if tipo == "expediente"
        else "https://apps2.mef.gob.pe/consulta-vfp-webapp/actionConsultaCertificado.jspx"
    )

    payload = {"anoEje": anio, "secEjec": unidad, "j_captcha": captcha}
    if tipo == "expediente":
        payload["expediente"] = numero
    else:
        payload["certificado"] = numero

    try:
        async with session.post(url_post, data=payload, timeout=25) as resp:
            html = await resp.text()
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error de conexión: {e}")
        await session.close()
        return ConversationHandler.END

    soup = BeautifulSoup(html, "html.parser")
    tabla = soup.find("table")

    if not tabla:
        print(f"❌ Captcha fallido por @{update.effective_user.username or update.effective_user.id}")
        await update.message.reply_text("❌ Captcha incorrecto o no se encontró información. Inténtelo nuevamente.")
        return await mostrar_captcha(update, context)

    data = []
    headers = [th.get_text(strip=True) for th in tabla.find_all("th")]
    for tr in tabla.find_all("tr")[1:]:
        row = [td.get_text(strip=True) for td in tr.find_all("td")]
        if row:
            data.append(row)

    if not data:
        await update.message.reply_text("⚠️ No se encontraron resultados para los datos ingresados.")
        await session.close()
        return ConversationHandler.END

    df = pd.DataFrame(data, columns=headers)
    archivo = f"{tipo}_{anio}_{numero}.xlsx"

    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)

    resumen = df.head(5).to_string(index=False)
    await update.message.reply_text(f"✅ Consulta completada:\n\n{resumen}")
    await update.message.reply_document(buffer, filename=archivo)

    print(f"✅ @{update.effective_user.username or update.effective_user.id} consultó {tipo} {anio}-{numero} correctamente.")

    await session.close()
    keyboard = [["Sí", "No"]]
    await update.message.reply_text(
        "¿Desea realizar otra consulta?",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    )
    return CONSULTA_FINAL


# --- CONSULTA FINAL ---
async def consulta_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    respuesta = update.message.text.strip().lower()
    if respuesta in ["sí", "si"]:
        keyboard = [["/consulta_exp", "/consulta_cert"]]
        await update.message.reply_text(
            "Seleccione el tipo de consulta:",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text("👋 Gracias por usar el bot. ¡Hasta luego!")
        return ConversationHandler.END


# --- MAIN ---
def main():
    print("🤖 Iniciando bot del MEF...")

    application = ApplicationBuilder().token("COLOCAR_TU_TOKEN_ID_TELEGRAM").build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("consulta_exp", consulta_exp),
            CommandHandler("consulta_cert", consulta_cert)
        ],
        states={
           PEDIR_ANIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, pedir_unidad)],
        PEDIR_UNIDAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, pedir_numero)],
        PEDIR_NUM: [MessageHandler(filters.TEXT & ~filters.COMMAND, mostrar_captcha)],
        PEDIR_CAPTCHA: [MessageHandler(filters.TEXT & ~filters.COMMAND, procesar_consulta)],
        CONSULTA_FINAL: [MessageHandler(filters.Regex("^(Sí|No|si|no)$"), consulta_final)],
        },
        fallbacks=[
           CommandHandler("start", start),
              CommandHandler("cancelar", cancelar)
            
            ],
        allow_reentry=True,  # 🔥 Permite reiniciar flujo sin reiniciar bot
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cancelar", cancelar))
    application.add_handler(conv_handler)

    print("✅ Bot iniciado y escuchando actualizaciones.")
    application.run_polling()


if __name__ == "__main__":
    main()
