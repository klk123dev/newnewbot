import requests # type: ignore
import asyncio
from telegram import Bot, Update # type: ignore
from telegram.ext import ( # type: ignore
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from flask import Flask # type: ignore
import threading

# Configuración
TOKEN = "7193589103:AAGK8lFn1lQ6Xbmupc9zc6RMcDAqKWxPayM"  # Reemplázalo por tu token de @BotFather
RA_URLS = {}  # Diccionario para almacenar URLs a monitorear: {chat_id: url}

# Inicialización
bot = Bot(token=TOKEN)
app = Flask(__name__)

# ---- COMANDOS DEL BOT ----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mensaje de bienvenida"""
    await update.message.reply_text(
        "🎟️ **Bienvenido al Monitor de Entradas**\n\n"
        "📌 **Comandos disponibles:**\n"
        "/monitor [url] - Monitorear un evento\n"
        "/stop - Detener monitoreo\n"
        "/status - Ver estado\n\n"
        "Ejemplo:\n"
        "/monitor https://www.residentadvisor.net/events/..."
    )

async def monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Añade una URL para monitorear"""
    chat_id = update.message.chat_id
    url = " ".join(context.args)
    
    if not url.startswith("http"):
        await update.message.reply_text("⚠️ ¡Debes enviar una URL válida!")
        return
    
    RA_URLS[chat_id] = url
    await update.message.reply_text(
        f"🔍 **Monitoreando:** {url}\n"
        f"⏱️ Revisando cada 3 segundos..."
    )
    
    # Inicia el hilo de monitoreo
    threading.Thread(target=check_ra_availability, args=(chat_id, url)).start()

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Detiene el monitoreo"""
    chat_id = update.message.chat_id
    if chat_id in RA_URLS:
        del RA_URLS[chat_id]
        await update.message.reply_text("⏹️ **Monitoreo detenido**")
    else:
        await update.message.reply_text("❌ No hay eventos en monitoreo")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el estado actual"""
    chat_id = update.message.chat_id
    if chat_id in RA_URLS:
        await update.message.reply_text(
            f"✅ **Activo**\n"
            f"📌 URL: {RA_URLS[chat_id]}\n"
            f"⏱️ Frecuencia: 3 segundos"
        )
    else:
        await update.message.reply_text("🛑 No hay eventos en monitoreo")

# ---- MONITOREO EN SEGUNDO PLANO ----
def check_ra_availability(chat_id: int, url: str):
    """Verifica disponibilidad de entradas cada 3 segundos"""
    while chat_id in RA_URLS:  # Solo si sigue activo
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept-Language": "en-US,en;q=0.9"
            }
            response = requests.get(url, headers=headers, timeout=5)
            
            # Detección mejorada (actualizada 2025)
            if "Tickets for this event are sold out" not in response.text.lower() and "agotado" not in response.text.lower():
                asyncio.run(
                    bot.send_message(
                        chat_id=chat_id,
                        text=f"🚨 **¡ENTRADAS DISPONIBLES!** 🎟️\n{url}"
                    )
                )
                del RA_URLS[chat_id]  # Deja de monitorear
                break
                
            time.sleep(3)  # type: ignore # Espera 3 segundos entre checks
            
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(10) # type: ignore

# ---- CONFIGURACIÓN DE FLASK (PARA RENDER) ----
@app.route('/')
def home():
    return "🤖 Bot activo - Monitoreando Resident Advisor"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

# ---- INICIALIZACIÓN ----
if __name__ == '__main__':
    # Inicia Flask en un hilo separado
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Configura el bot de Telegram
    application = Application.builder().token(TOKEN).build()
    
    # Manejadores de comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("monitor", monitor))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("status", status))
    
    print("🤖 Bot iniciado correctamente!")
    application.run_polling()