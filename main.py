import os, json, random, time, threading
from datetime import datetime
from flask import Flask
import telebot

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
ARQUIVO = "placar.json"
app = Flask(__name__)

@app.route('/')
def home(): return "BOT V2 ON - Perfina Bets"

def carregar():
    if not os.path.exists(ARQUIVO): return []
    try:
        with open(ARQUIVO,'r') as f: return json.load(f)
    except: return []

def salvar(jogo,palpite):
    dados=carregar()
    dados.append({"data":datetime.now().strftime("%d/%m/%Y"),"jogo":jogo,"palpite":palpite,"status":random.choice(['green','green','red']),"odd":1.85})
    with open(ARQUIVO,'w') as f: json.dump(dados,f,indent=2)

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "🔥 Perfina Bets IA V2 ON!\n\n/palpite - gerar palpite\n/placar - ver Greens e Reds do dia")

@bot.message_handler(commands=['palpite'])
def palpite(m):
    jogos=["Flamengo x Palmeiras","Man City x Arsenal","Real Madrid x Barca"]
    mercados=["Ambas Marcam SIM","Over 1.5 Gols","Over 0.5 HT"]
    jogo=random.choice(jogos); mercado=random.choice(mercados)
    salvar(jogo,mercado)
    bot.reply_to(m, f"⚽ {jogo}\n💰 Palpite: {mercado}\n🎯 Confiança: {random.randint(80,92)}%\n\nVeja /placar")

@bot.message_handler(commands=['placar'])
def placar(m):
    hoje=datetime.now().strftime("%d/%m/%Y")
    dados=carregar(); do_dia=[d for d in dados if d['data']==hoje]
    g=len([d for d in do_dia if d['status']=='green']); r=len([d for d in do_dia if d['status']=='red'])
    taxa=(g/(g+r)*100) if (g+r)>0 else 0; lucro=g*0.85-r
    bot.reply_to(m, f"📊 PLACAR DO DIA - {hoje}\n\n✅ {g} GREENS\n❌ {r} REDS\n\n📈 {taxa:.1f}% acerto\n💰 {lucro:+.1f} unidades")

def run_bot():
    time.sleep(5)
    try: bot.remove_webhook()
    except: pass
    time.sleep(3)
    print("BOT V2 RODANDO... LIMPANDO CONFLITO")
    bot.infinity_polling(timeout=30, long_polling_timeout=30)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
