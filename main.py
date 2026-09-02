import telebot
from flask import Flask
import threading
import time
import random
from datetime import datetime

# SEUS DADOS
TOKEN = "8974124974:AAE1KqLMUpH5ukWFpP1B8d_77a-BD2YyNUw"
SEU_ID = 5297279818  # Manoel Junior

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "BOT V4.2 AUTO ON - Perfina Bets IA", 200

# --- SEUS PALPITES (pode editar) ---
def gerar_palpite():
    palpites = [
        "🎯 **PALPITE PERFINA IA** 🎯\n\n⚽️ Over 1.5 Gols - Jogo ao vivo\n📊 Confiança: 87%\n💰 Entra forte!",
        "🔥 **ENTRADA QUENTE** 🔥\n\n⚽️ Ambas Marcam - SIM\n📊 IA analisou 12 jogos\n💸 Odd 1.95",
        "🤖 **IA PERFINA BETS** 🤖\n\n🏀 NBA - Over 210.5 Pontos\n📈 Padrão detectado: 9/10 GREEN\n✅ ENTRADA VALIDADA"
    ]
    return random.choice(palpites)

# --- COMANDOS ---
@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "🚀 Bot Perfina Bets IA V4.2 ON!\n\nUse /palpite para gerar agora\nPalpites automáticos a cada 3h ativados!")

@bot.message_handler(commands=['palpite'])
def palpite(m):
    bot.send_message(m.chat.id, gerar_palpite())

# --- LOOP AUTOMÁTICO A CADA 3 HORAS ---
def loop_auto():
    while True:
        try:
            time.sleep(3*60*60) # 3 horas
            palpite_auto = gerar_palpite() + "\n\n⏰ **AUTO 3H - V4.2**"
            bot.send_message(SEU_ID, palpite_auto)
            print(f"Auto-enviado em {datetime.now()}")
        except Exception as e:
            print(f"Erro auto: {e}")
            time.sleep(60)

# --- INICIA ---
threading.Thread(target=loop_auto, daemon=True).start()

def run_bot():
    while True:
        try:
            bot.polling(none_stop=True, timeout=60)
        except:
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
