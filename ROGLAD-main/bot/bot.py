#from .config import *
import telebot, threading, os, time as ti
from telebot.types import InlineKeyboardMarkup,InlineKeyboardButton

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from bussiness.models import AlertaAdmin

try:
    TOKEN = os.environ.get('TOKEN_BOT')
    ADMIN1_ID = int(os.environ.get('ADMIN1_ID'))
except:
    TOKEN = '7611854559:AAH0lfmDRC0a9vX0MsRNOvVLSuQKz5kVs38'
    ADMIN1_ID = 0
    
bot = telebot.TeleBot(TOKEN)





# ~ COMANDS ~
@bot.message_handler(commands=["start"])
def cmd_chat_id(message):
    if message.chat.id == ADMIN1_ID:
        m = "<b>Bienvenida Anaily a tu chismoso personal 😉</b>\n"
        m += "<i>Mi padre Rafael me creó con el propósito de mantenerte informada en </i><b>TIEMPO REAL</b> <i>de cada cambio que suceda en ROGLAD</i>\n"
        m += "Espero serte de utilidad 😊"
        bot.send_message(message.chat.id, m, parse_mode="html", disable_web_page_preview=True)
    else:
        bot.send_message(message.chat.id, f"No tienes acceso 💩 (<code>{message.chat.id}</code>)", parse_mode="html", disable_web_page_preview=True)

# ~ COMANDS ~
@bot.message_handler(commands=["cmd_chat_id"])
def cmd_chat_id(message):
    bot.send_message(message.chat.id, str(message.chat.id))


def send_message(message=str,alertId=None):
    bot.send_chat_action(ADMIN1_ID, "typing")
    if alertId:
        markup = InlineKeyboardMarkup(row_width=1)
        btn_success = InlineKeyboardButton("✅ Marcar como leido",callback_data=f"{alertId}")
        markup.add(btn_success)
        bot.send_message(ADMIN1_ID,message,parse_mode="html",disable_web_page_preview=True,reply_markup=markup)
    else:
        bot.send_message(ADMIN1_ID,message,parse_mode="html",disable_web_page_preview=True)

@bot.callback_query_handler(func=lambda x:True)
def response_buttons(call):
    try:
        chat_id = call.from_user.id
        message_id = call.message.id
        message_text = call.message.text
        alert_id = call.data

        alert = AlertaAdmin.objects.get(id = alert_id)
        alert.activo = False
        alert.save()
        
        bot.edit_message_text(message_text ,chat_id,message_id,parse_mode="html")
    
    except Exception as e:
        bot.send_message(ADMIN1_ID,f"⚠️ Ha ocurrido un error: {e}",parse_mode="html",disable_web_page_preview=True)


#def bot_infinity_polling():
#    bot.infinity_polling()

#threadBot = threading.Thread(name="bot_infinity_polling", target=bot_infinity_polling)
#threadBot.start()

#if not settings.DEBUG:
try:
    bot.remove_webhook()
    ti.sleep(1)
    URL_WEBHOOK = os.environ.get('URL_WEBHOOK')
    bot.set_webhook(url=f"{URL_WEBHOOK}remote-control/")
except:pass

