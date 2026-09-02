import os
import telebot
from flask import Flask
import threading
from datetime import datetime

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN não definido no Environment do Render!")

SEU_ID = 5297279818
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "BOT V4.3 AUTO ON", 200

placar = {"green":0,"red":0,"pendente":0}

@bot.message_handler(commands=['start','palpite','placar','green','red','reset'])
def all_cmd(m):
    txt = m.text.lower()
    if '/start' in txt:
        bot.reply_to(m, "⚽ /palpite\n✅ /green\n❌ /red\n📊 /placar\n🔄 /reset")
    elif '/palpite' in txt:
        placar["pendente"]+=1
        bot.send_message(m.chat.id, "🤖 IA: Over 1.5 Gols @1.42 - 88% conf - Use /green ou /red depois")
    elif '/green' in txt:
        placar["green"]+=1
        placar["pendente"]=max(0, placar["pendente"]-1)
        bot.reply_to(m, "✅ GREEN!")
    elif '/red' in txt:
        placar["red"]+=1
        placar["pendente"]=max(0, placar["pendente"]-1)
        bot.reply_to(m, "❌ RED!")
    elif '/placar' in txt:
        bot.send_message(m.chat.id, f"📊 {placar}")
    elif '/reset' in txt:
        placar.update({"green":0,"red":0,"pendente":0})
        bot.reply_to(m, "🔄 Zerado!")

def run_bot():
    print(">>> BOT INICIANDO COM TOKEN NOVO <<<")
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
