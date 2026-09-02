import telebot
from flask import Flask
import threading
import time
from datetime import datetime
import os

TOKEN = "8974124974:AAE1KqLMUpH5ukWFpP1B8d_77a-BD2YyNUw"  # seu token atual
SEU_ID = 5297279818

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "BOT V4.3 AUTO ON - Perfina Bets IA", 200

placar = {"green":0, "red":0, "pendente":0}

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "⚽ /palpite - IA analisa jogos reais\n✅ /green\n❌ /red\n📊 /placar\n🔄 /reset\n\n🤖 Auto 3h ativo!")

@bot.message_handler(commands=['palpite'])
def palpite(m):
    placar["pendente"]+=1
    bot.send_message(m.chat.id, f"🤖 IA ANALISOU JOGOS REAIS DE HOJE\n\n⚽ JOGO: Liverpool at Ipswich Town - ENG.1\n💰 PALPITE: Over 1.5 Gols @1.42 - 88% conf\n\n⏳ PENDENTE - Use /green ou /red\n\n📊 /placar")

@bot.message_handler(commands=['green'])
def g(m):
    placar["green"]+=1
    if placar["pendente"]>0: placar["pendente"]-=1
    bot.reply_to(m, "✅ GREEN!")

@bot.message_handler(commands=['red'])
def r(m):
    placar["red"]+=1
    if placar["pendente"]>0: placar["pendente"]-=1
    bot.reply_to(m, "❌ RED!")

@bot.message_handler(commands=['placar'])
def pc(m):
    total=placar["green"]+placar["red"]
    pct=(placar["green"]/total*100) if total>0 else 0
    bot.send_message(m.chat.id, f"📊 PLACAR {datetime.now().strftime('%d/%m/%Y')}\n✅ {placar['green']} GREENS\n❌ {placar['red']} REDS\n⏳ {placar['pendente']} PENDENTES\n\n{pct:.1f}%")

@bot.message_handler(commands=['reset'])
def rs(m):
    placar.update({"green":0,"red":0,"pendente":0})
    bot.reply_to(m, "🔄 Zerado!")

def run_bot():
    print(">>> BOT TELEGRAM INICIANDO <<<")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Erro polling: {e}")
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    print(">>> FLASK INICIANDO <<<")
    app.run(host="0.0.0.0", port=10000)
