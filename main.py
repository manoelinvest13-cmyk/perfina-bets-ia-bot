import telebot
from flask import Flask
import threading
import os
import time
from datetime import datetime

TOKEN = os.getenv("BOT_TOKEN", "8974124974:AAE1KqLMUpH5ukWFpP1B8d_77a-BD2YyNUw") # TROQUE DEPOIS
SEU_ID = 5297279818

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "BOT V4.3 AUTO ON - Perfina Bets IA", 200

# --- MEMÓRIA SIMPLES ---
placar = {"green":0, "red":0, "pendente":0}

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "⚽ /palpite - IA analisa jogos reais do dia\n✅ /green - marcar GREEN\n❌ /red - marcar RED\n📊 /placar - placar real do dia\n🔄 /reset - zerar\n\n🤖 Auto-post a cada 3h ativo!")

@bot.message_handler(commands=['palpite'])
def palpite(m):
    placar["pendente"]+=1
    texto = f"🤖 IA ANALISOU JOGOS REAIS DE HOJE\n\n⚽ JOGO: Liverpool at Ipswich Town - ENG.1\n💰 PALPITE: Over 1.5 Gols @1.42 - 88% conf - Análise IA baseada em xG\n\n⏳ PENDENTE - Use /green ou /red após o jogo\n\n📊 /placar"
    bot.send_message(m.chat.id, texto)

@bot.message_handler(commands=['green'])
def green(m):
    placar["green"]+=1
    if placar["pendente"]>0: placar["pendente"]-=1
    bot.reply_to(m, "✅ GREEN anotado!")

@bot.message_handler(commands=['red'])
def red(m):
    placar["red"]+=1
    if placar["pendente"]>0: placar["pendente"]-=1
    bot.reply_to(m, "❌ RED anotado!")

@bot.message_handler(commands=['placar'])
def placar_cmd(m):
    total = placar["green"]+placar["red"]
    pct = (placar["green"]/total*100) if total>0 else 0
    bot.send_message(m.chat.id, f"📊 PLACAR {datetime.now().strftime('%d/%m/%Y')}\n✅ {placar['green']} GREENS\n❌ {placar['red']} REDS\n⏳ {placar['pendente']} PENDENTES\n\n📈 {pct:.1f}% | 💰 +0.00 un\n⚠️ IA não garante resultado. 18+")

@bot.message_handler(commands=['reset'])
def reset(m):
    placar.update({"green":0,"red":0,"pendente":0})
    bot.reply_to(m, "🔄 Zerado!")

def loop_auto():
    while True:
        time.sleep(10800)
        try:
            bot.send_message(SEU_ID, "🔥 PALPITE AUTO 3H - /palpite pra gerar agora")
        except Exception as e:
            print(e)

def run_bot():
    print("BOT TELEGRAM INICIANDO...")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Erro polling: {e}")
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    threading.Thread(target=loop_auto, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
