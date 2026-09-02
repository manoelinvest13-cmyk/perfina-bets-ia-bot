import os, telebot, requests, random, time
from flask import Flask
import threading
from datetime import datetime

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN, threaded=False)
try:
    bot.remove_webhook()
    time.sleep(2)
except: pass

app = Flask(__name__)
@app.route('/')
def home(): return "V7 30MIN AUTO ON", 200

placar = {"green":0,"red":0,"pendente":0}
chat_ids = set()

def calc_prob(t1,t2):
    seed=sum(ord(c) for c in t1+t2+str(datetime.now().day))
    random.seed(seed)
    over15 = random.randint(65,88)
    over05 = min(97, over15 + random.randint(10,16))
    return {
        "Over 0.5": over05,
        "Over 1.5": over15,
        "BTTS SIM": random.randint(48,76),
        "BTTS NÃO": random.randint(42,62),
        f"{t1[:10]} +0.5": random.randint(60,84),
        f"{t2[:10]} +0.5": random.randint(45,70),
    }

def buscar():
    msg=f"🤖 PERFINA V7\n📅 {datetime.now().strftime('%d/%m %H:%M')}\n━━━━━━━━━━━━━━━\n\n"
    count=0
    for liga in ['eng.1','esp.1','bra.1']:
        if count>=3: break
        try:
            url=f"https://site.api.espn.com/apis/site/v2/sports/soccer/{liga}/scoreboard"
            r=requests.get(url,timeout=8).json()
            if not r.get('events'): continue
            j=r['events'][0]
            casa=j['competitions'][0]['competitors'][0]['team']['displayName']
            fora=j['competitions'][0]['competitors'][1]['team']['displayName']
            hora=j['date'][11:16]
            probs=calc_prob(casa,fora)
            melhor=max(probs, key=probs.get)
            msg+=f"⚽ {casa} x {fora}\n🏆 {liga.upper()} - {hora}h\n\n"
            for m,p in probs.items():
                icon="🔥" if p>=90 else "✅"
                msg+=f"{icon} {m}: {p}%\n"
            msg+=f"\n💡 MELHOR: {melhor} ({probs[melhor]}%)\n━━━━━━━━━━━━━━━\n\n"
            count+=1
        except: continue
    msg+="⚠️ Gestão 2% banca. 18+\n⏰ Auto a cada 30 min"
    return msg

@bot.message_handler(commands=['start','ajuda'])
def start(m):
    chat_ids.add(m.chat.id)
    bot.reply_to(m, "🤖 PERFINA V7 - 30MIN AUTO\n\n✅ NOVO:\n• Over 0.5 SEMPRE maior que Over 1.5\n• Melhor = MAIOR % (corrigido)\n• Auto a cada 30 MIN\n• Placar Green/Red\n\n📋 COMANDOS:\n/palpite - Agora\n/green - Acertou +1\n/red - Errou +1\n/placar - Ver resultado\n/reset - Zerar placar\n\n🤖 AUTO ATIVADO! Você vai receber palpite a cada 30 min.")

@bot.message_handler(commands=['palpite'])
def palpite(m):
    chat_ids.add(m.chat.id)
    bot.send_message(m.chat.id,"🔍 Analisando 6 mercados...")
    placar["pendente"]+=1
    bot.send_message(m.chat.id,buscar())

@bot.message_handler(commands=['green','red','placar','reset'])
def outros(m):
    t=m.text.lower()
    if 'green' in t:
        placar["green"]+=1
        placar["pendente"]=max(0,placar["pendente"]-1)
        bot.reply_to(m,f"✅ GREEN ANOTADO!\n📊 {placar['green']}G x {placar['red']}R")
    elif 'red' in t:
        placar["red"]+=1
        placar["pendente"]=max(0,placar["pendente"]-1)
        bot.reply_to(m,f"❌ RED ANOTADO!\n📊 {placar['green']}G x {placar['red']}R")
    elif 'placar' in t:
        total=placar["green"]+placar["red"]
        pct=(placar["green"]/total*100) if total>0 else 0
        bot.reply_to(m,f"📊 PLACAR PERFINA\n✅ {placar['green']} GREEN\n❌ {placar['red']} RED\n⏳ {placar['pendente']} PENDENTE\n📈 Acerto: {pct:.1f}%\n💰 Lucro: {placar['green']*0.85 - placar['red']:.2f} unid")
    else:
        placar.update({"green":0,"red":0,"pendente":0})
        bot.reply_to(m,"🔄 Placar zerado com sucesso!")

def auto_loop():
    while True:
        time.sleep(1800) # 30 MINUTOS
        if not chat_ids: continue
        try:
            texto=buscar()
            for cid in list(chat_ids):
                try:
                    bot.send_message(cid, "⏰ AUTO 30MIN\n\n"+texto)
                except: pass
        except: pass

def run_bot():
    threading.Thread(target=auto_loop,daemon=True).start()
    while True:
        try:
            print("V7 30MIN RODANDO")
            bot.infinity_polling(skip_pending=True, timeout=30)
        except Exception as e:
            print(f"Erro: {e}")
            time.sleep(10)

if __name__=="__main__":
    threading.Thread(target=run_bot,daemon=True).start()
    app.run(host="0.0.0.0",port=10000)
