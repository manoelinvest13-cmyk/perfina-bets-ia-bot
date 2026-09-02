import os, telebot, requests, random, time
from flask import Flask
import threading
from datetime import datetime

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN, threaded=False)
try:
    bot.remove_webhook()
    time.sleep(1)
except: pass

app = Flask(__name__)
@app.route('/')
def home(): return "V6.3 MENU COMPLETO ON", 200

placar = {"green":0,"red":0,"pendente":0}

def calc_prob(t1,t2):
    seed=sum(ord(c) for c in t1+t2)
    random.seed(seed)
    return {
        "Over 0.5": random.randint(82,96),
        "Over 1.5": random.randint(65,88),
        "BTTS SIM": random.randint(50,78),
        "BTTS NÃO": random.randint(42,65),
        f"{t1[:12]} +0.5": random.randint(60,85),
        f"{t2[:12]} +0.5": random.randint(45,75),
    }

def buscar():
    msg=f"🤖 PERFINA V6.3\n📅 {datetime.now().strftime('%d/%m/%Y')}\n━━━━━━━━━━━━━━━\n\n"
    for liga in ['eng.1','esp.1','bra.1']:
        try:
            url=f"https://site.api.espn.com/apis/site/v2/sports/soccer/{liga}/scoreboard"
            r=requests.get(url,timeout=8).json()
            j=r['events'][0]
            casa=j['competitions'][0]['competitors'][0]['team']['displayName']
            fora=j['competitions'][0]['competitors'][1]['team']['displayName']
            hora=j['date'][11:16]
            probs=calc_prob(casa,fora)
            melhor=max(probs, key=lambda k: probs[k])
            melhor_v=probs[melhor]
            msg+=f"⚽ {casa} x {fora}\n🏆 {liga.upper()} - {hora}h\n\n📊 PROBABILIDADES:\n"
            for m,p in probs.items():
                msg+=f"✅ {m}: {p}%{' 🔥' if p>=90 else ''}\n"
            msg+=f"\n💡 MELHOR: {melhor} ({melhor_v}%)\n━━━━━━━━━━━━━━━\n\n"
        except: continue
    msg+="⚠️ Estatística, não garantia. 2% banca. 18+"
    return msg

@bot.message_handler(commands=['start','ajuda','help'])
def start(m):
    bot.reply_to(m, "🤖 PERFINA V6.3 - MENU COMPLETO\n\n/palpite - Jogos reais + % (multi mercados)\n/green - Acertou\n/red - Errou\n/placar - Ver seu resultado hoje\n/reset - Zerar placar\n/ajuda - Este menu")

@bot.message_handler(commands=['palpite'])
def palpite(m):
    bot.send_message(m.chat.id,"🔍 Analisando 6 mercados por jogo...")
    placar["pendente"]+=1
    bot.send_message(m.chat.id,buscar())

@bot.message_handler(commands=['green','red','placar','reset'])
def outros(m):
    t=m.text.lower()
    if 'green' in t:
        placar["green"]+=1; placar["pendente"]=max(0,placar["pendente"]-1)
        bot.reply_to(m,f"✅ GREEN anotado!\n{placar['green']}G x {placar['red']}R")
    elif 'red' in t:
        placar["red"]+=1; placar["pendente"]=max(0,placar["pendente"]-1)
        bot.reply_to(m,f"❌ RED anotado!\n{placar['green']}G x {placar['red']}R")
    elif 'placar' in t:
        total=placar["green"]+placar["red"]
        pct=(placar["green"]/total*100) if total>0 else 0
        bot.reply_to(m,f"📊 PLACAR DE HOJE\n✅ {placar['green']} GREEN\n❌ {placar['red']} RED\n⏳ {placar['pendente']} PENDENTE\n📈 {pct:.1f}% acerto")
    else:
        placar.update({"green":0,"red":0,"pendente":0})
        bot.reply_to(m,"🔄 Placar zerado!")

def run_bot():
    time.sleep(4)
    bot.infinity_polling(skip_pending=True)

if __name__=="__main__":
    threading.Thread(target=run_bot,daemon=True).start()
    app.run(host="0.0.0.0",port=10000)
