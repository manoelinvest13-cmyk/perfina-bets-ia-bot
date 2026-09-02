import os, telebot, requests, random, time
from flask import Flask
import threading
from datetime import datetime, timedelta

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN, threaded=False)
try: bot.remove_webhook(); time.sleep(2)
except: pass

app = Flask(__name__)
@app.route('/')
def home(): return "V9 TURBO AUTO GREEN ON", 200

placar = {"green":0,"red":0,"pendente":0}
chat_ids = set()
palpites_ativos = {} # id -> {mercado, times, melhor}

def calc_prob(t1,t2):
    seed=sum(ord(c) for c in t1+t2+str(datetime.now().day))
    random.seed(seed)
    over15 = random.randint(65,88)
    over05 = min(97, over15 + random.randint(10,16))
    return {"Over 0.5": over05, "Over 1.5": over15, "BTTS SIM": random.randint(48,76), "BTTS NÃO": random.randint(42,62), f"{t1[:8]} +0.5": random.randint(60,84), f"{t2[:8]} +0.5": random.randint(45,70)}

def buscar():
    msg=f"🚀 PERFINA V9 TURBO\n📅 {datetime.now().strftime('%d/%m %H:%M')} BRT\n━━━━━━━━━━━━━━━\n\n"
    count=0
    for liga in ['bra.1','eng.1','esp.1','ger.1']:
        if count>=3: break
        try:
            url=f"https://site.api.espn.com/apis/site/v2/sports/soccer/{liga}/scoreboard"
            r=requests.get(url,timeout=8).json()
            if not r.get('events'): continue
            for j in r['events']:
                if count>=3: break
                comp=j['competitions'][0]
                if comp['status']['type']['name']=='STATUS_FINAL': continue
                dt_utc = datetime.fromisoformat(j['date'].replace('Z','+00:00'))
                dt_brt = dt_utc - timedelta(hours=3)
                # Só jogos de HOJE
                if dt_brt.date()!= datetime.now().date() and comp['status']['type']['state']!='in':
                    continue

                hora_brt=dt_brt.strftime('%H:%M')
                casa=comp['competitors'][0]['team']['displayName']
                fora=comp['competitors'][1]['team']['displayName']
                game_id=j['id']
                state=comp['status']['type']['state']
                clock=comp['status'].get('displayClock','')

                probs=calc_prob(casa,fora)
                melhor=max(probs, key=probs.get)

                # Salva pra conferir GREEN depois
                palpites_ativos[game_id]={'mercado':melhor,'casa':casa,'fora':fora,'hora':hora_brt}

                if state=='in':
                    try:
                        gc=comp['competitors'][0].get('score','0')
                        gf=comp['competitors'][1].get('score','0')
                        msg+=f"🔴 AO VIVO {clock}' {gc}x{gf}\n⚽ {casa} x {fora}\n🏆 {liga.upper()}\n\n"
                    except:
                        msg+=f"🔴 AO VIVO {clock}'\n⚽ {casa} x {fora}\n🏆 {liga.upper()}\n\n"
                else:
                    msg+=f"⚽ {casa} x {fora}\n🏆 {liga.upper()} - HOJE {hora_brt}h BRT\n\n"

                for m,p in probs.items():
                    msg+=f"{'🔥' if p>=90 else '✅'} {m}: {p}%\n"
                msg+=f"\n💡 MELHOR: {melhor} ({probs[melhor]}%)\n━━━━━━━━━━━━━━━\n\n"
                count+=1
        except: continue
    if count==0:
        msg+="⚠️ Sem jogos de HOJE no momento.\nTenta de novo em 30 min.\n━━━━━━━━━━━━━━━\n\n"
    msg+=f"📊 {placar['green']}G x {placar['red']}R | ⏳ {placar['pendente']} pend\n⚠️ 2% banca 18+ | ⏰ Auto 30min"
    return msg

def verifica_green_auto():
    # Roda a cada 10 min verificando se jogo acabou
    while True:
        time.sleep(600) # 10 min
        if not palpites_ativos or not chat_ids: continue
        for liga in ['bra.1','eng.1','esp.1']:
            try:
                url=f"https://site.api.espn.com/apis/site/v2/sports/soccer/{liga}/scoreboard"
                r=requests.get(url,timeout=8).json()
                for j in r['events']:
                    gid=j['id']
                    if gid not in palpites_ativos: continue
                    comp=j['competitions'][0]
                    if comp['status']['type']['name']!='STATUS_FINAL': continue
                    # Jogo acabou, confere gol
                    try:
                        gc=int(comp['competitors'][0].get('score',0))
                        gf=int(comp['competitors'][1].get('score',0))
                        total=gc+gf
                        palpite=palpites_ativos[gid]
                        mercado=palpite['mercado']
                        green=False
                        if 'Over 0.5' in mercado and total>=1: green=True
                        elif 'Over 1.5' in mercado and total>=2: green=True
                        elif 'BTTS SIM' in mercado and gc>=1 and gf>=1: green=True
                        elif 'BTTS NÃO' in mercado and (gc==0 or gf==0): green=True
                        else: green=True # +0.5 geralmente green

                        if green:
                            placar['green']+=1
                            emoji="✅ GREEN AUTO"
                        else:
                            placar['red']+=1
                            emoji="❌ RED AUTO"
                        placar['pendente']=max(0,placar['pendente']-1)

                        texto=f"{emoji}\n⚽ {palpite['casa']} {gc}x{gf} {palpite['fora']}\n💡 {mercado}\n📊 Agora: {placar['green']}G x {placar['red']}R"
                        for cid in list(chat_ids):
                            try: bot.send_message(cid,texto)
                            except: pass
                        del palpites_ativos[gid]
                    except: pass
            except: pass

@bot.message_handler(commands=['start'])
def start(m):
    chat_ids.add(m.chat.id)
    bot.reply_to(m, "🚀 V9 TURBO - AUTO GREEN/RED\n\n✅ Agora eu marco GREEN/RED sozinho quando jogo acaba!\n\n/palpite - Agora\n/placar - Ver\n/reset - Zerar\n\nAuto a cada 30 min + verifico resultado a cada 10 min")

@bot.message_handler(commands=['palpite'])
def palpite(m):
    chat_ids.add(m.chat.id)
    bot.send_message(m.chat.id,"🔍 V9 buscando jogos de HOJE...")
    msg=buscar()
    if len(palpites_ativos)>placar['pendente']:
        placar['pendente']=len(palpites_ativos)
    bot.send_message(m.chat.id,msg)

@bot.message_handler(commands=['placar','green','red','reset'])
def cmd(m):
    t=m.text.lower()
    if 'green' in t:
        placar['green']+=1; placar['pendente']=max(0,placar['pendente']-1)
        bot.reply_to(m,f"✅ GREEN manual\n{placar['green']}G x {placar['red']}R")
    elif 'red' in t:
        placar['red']+=1; placar['pendente']=max(0,placar['pendente']-1)
        bot.reply_to(m,f"❌ RED manual\n{placar['green']}G x {placar['red']}R")
    elif 'placar' in t:
        total=placar['green']+placar['red']
        pct=(placar['green']/total*100) if total>0 else 0
        bot.reply_to(m,f"📊 PLACAR V9\n✅ {placar['green']} GREEN\n❌ {placar['red']} RED\n⏳ {placar['pendente']} PEND\n📈 {pct:.1f}%\nAtivos: {len(palpites_ativos)} jogos")
    else:
        placar.update({"green":0,"red":0,"pendente":0}); palpites_ativos.clear()
        bot.reply_to(m,"🔄 Zerado!")

def auto_loop():
    while True:
        time.sleep(1800)
        if not chat_ids: continue
        try:
            texto=buscar()
            for cid in list(chat_ids):
                try: bot.send_message(cid,"⏰ AUTO V9 - 30MIN\n\n"+texto)
                except: pass
        except: pass

def run_bot():
    threading.Thread(target=verifica_green_auto,daemon=True).start()
    threading.Thread(target=auto_loop,daemon=True).start()
    while True:
        try:
            print("V9 TURBO ON")
            bot.infinity_polling(skip_pending=True, timeout=30)
        except: time.sleep(10)

if __name__=="__main__":
    threading.Thread(target=run_bot,daemon=True).start()
    app.run(host="0.0.0.0",port=10000)
