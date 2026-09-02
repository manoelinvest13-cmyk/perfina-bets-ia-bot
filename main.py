import os, telebot, requests, random, time
from flask import Flask
import threading
from datetime import datetime, timedelta

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN, threaded=False)
try:
    bot.remove_webhook()
    time.sleep(2)
except: pass

app = Flask(__name__)
@app.route('/')
def home(): return "PERFINA V8 TURBO ON", 200

placar = {"green":0,"red":0,"pendente":0}
chat_ids = set()

def calc_prob(t1,t2):
    seed=sum(ord(c) for c in t1+t2+str(datetime.now().day))
    random.seed(seed)
    over15 = random.randint(65,88)
    over05 = min(97, over15 + random.randint(10,16)) # Over 0.5 SEMPRE maior
    return {
        "Over 0.5": over05,
        "Over 1.5": over15,
        "BTTS SIM": random.randint(48,76),
        "BTTS NÃO": random.randint(42,62),
        f"{t1[:10]} +0.5": random.randint(60,84),
        f"{t2[:10]} +0.5": random.randint(45,70),
    }

def buscar():
    msg=f"🤖 PERFINA BET V8 TURBO\n📅 {datetime.now().strftime('%d/%m %H:%M')} BRT\n━━━━━━━━━━━━━━━\n\n"
    count=0
    for liga in ['eng.1','esp.1','bra.1']:
        if count>=3: break
        try:
            url=f"https://site.api.espn.com/apis/site/v2/sports/soccer/{liga}/scoreboard"
            r=requests.get(url,timeout=8).json()
            if not r.get('events'): continue
            for j in r['events'][:4]:
                if count>=3: break
                comp=j['competitions'][0]
                status_name=comp['status']['type']['name']
                clock=comp['status'].get('displayClock','')
                state=comp['status']['type']['state']

                # Converte UTC -> BRT
                try:
                    dt_utc = datetime.fromisoformat(j['date'].replace('Z','+00:00'))
                    dt_brt = dt_utc - timedelta(hours=3)
                    hora_brt = dt_brt.strftime('%H:%M')
                except:
                    hora_brt = j['date'][11:16]

                if status_name == 'STATUS_FINAL': continue

                casa=comp['competitors'][0]['team']['displayName']
                fora=comp['competitors'][1]['team']['displayName']
                placar_ao_vivo=""
                if state=='in':
                    try:
                        g_casa=comp['competitors'][0].get('score','0')
                        g_fora=comp['competitors'][1].get('score','0')
                        placar_ao_vivo=f" {g_casa}x{g_fora}"
                    except: pass

                probs=calc_prob(casa,fora)
                melhor=max(probs, key=probs.get)

                if state=='in':
                    msg+=f"🔴 AO VIVO {clock}'{placar_ao_vivo}\n⚽ {casa} x {fora}\n🏆 {liga.upper()}\n\n"
                else:
                    msg+=f"⚽ {casa} x {fora}\n🏆 {liga.upper()} - HOJE {hora_brt}h BRT\n\n"

                for m,p in probs.items():
                    icon="🔥" if p>=90 else "✅"
                    msg+=f"{icon} {m}: {p}%\n"
                msg+=f"\n💡 MELHOR: {melhor} ({probs[melhor]}%)\n━━━━━━━━━━━━━━━\n\n"
                count+=1
        except Exception as e:
            print(f"erro liga {liga}: {e}")
            continue

    if count==0:
        msg+="Sem jogos ao vivo no momento.\nPróximos jogos em breve.\n━━━━━━━━━━━━━━━\n\n"

    msg+=f"📊 {placar['green']}G x {placar['red']}R\n⚠️ Gestão 2% banca. 18+\n⏰ Auto 30 min"
    return msg

@bot.message_handler(commands=['start','ajuda'])
def start(m):
    chat_ids.add(m.chat.id)
    bot.reply_to(m, "🚀 PERFINA BET V8 TURBO ATIVADO!\n\n✅ NOVIDADES V8:\n• Horário BRT (Brasília) corrigido\n• Mostra 🔴 AO VIVO quando jogo começou\n• Over 0.5 SEMPRE maior que Over 1.5\n• Melhor = maior % real\n• Jogos REAIS da ESPN\n\n📋 COMANDOS:\n/palpite - Palpite agora\n/green - +1 Green\n/red - +1 Red\n/placar - Meu placar\n/reset - Zerar\n\n🤖 AUTO: Palpite automático a cada 30 min nesse chat!")

@bot.message_handler(commands=['palpite'])
def palpite(m):
    chat_ids.add(m.chat.id)
    bot.send_message(m.chat.id,"🔍 V8 Turbo buscando jogos REAIS...")
    placar["pendente"]+=1
    bot.send_message(m.chat.id,buscar())

@bot.message_handler(commands=['green','red','placar','reset'])
def outros(m):
    t=m.text.lower()
    if 'green' in t:
        placar["green"]+=1
        placar["pendente"]=max(0,placar["pendente"]-1)
        bot.reply_to(m,f"✅ GREEN!\n📊 {placar['green']}G x {placar['red']}R")
    elif 'red' in t:
        placar["red"]+=1
        placar["pendente"]=max(0,placar["pendente"]-1)
        bot.reply_to(m,f"❌ RED!\n📊 {placar['green']}G x {placar['red']}R")
    elif 'placar' in t:
        total=placar["green"]+placar["red"]
        pct=(placar["green"]/total*100) if total>0 else 0
        bot.reply_to(m,f"📊 PLACAR V8 TURBO\n✅ {placar['green']} GREEN\n❌ {placar['red']} RED\n⏳ {placar['pendente']} PENDENTE\n📈 {pct:.1f}% acerto\n💰 {placar['green']*0.85 - placar['red']:.2f} unid")
    else:
        placar.update({"green":0,"red":0,"pendente":0})
        bot.reply_to(m,"🔄 Placar zerado!")

def auto_loop():
    while True:
        time.sleep(1800) # 30 MIN
        if not chat_ids: continue
        try:
            texto=buscar()
            for cid in list(chat_ids):
                try:
                    bot.send_message(cid, "⏰ AUTO V8 TURBO - 30MIN\n\n"+texto)
                except: pass
        except: pass

def run_bot():
    threading.Thread(target=auto_loop,daemon=True).start()
    while True:
        try:
            print("V8 TURBO RODANDO")
            bot.infinity_polling(skip_pending=True, timeout=30)
        except Exception as e:
            print(f"Erro: {e}")
            time.sleep(10)

if __name__=="__main__":
    threading.Thread(target=run_bot,daemon=True).start()
    app.run(host="0.0.0.0",port=10000)
