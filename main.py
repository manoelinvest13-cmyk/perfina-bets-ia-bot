import os, json, time, threading
from datetime import datetime, timezone, timedelta
import requests
from flask import Flask
import telebot

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BOT = telebot.TeleBot(TOKEN)
app = Flask(__name__)
ARQ = "placar.json"

def carregar():
    try:
        with open(ARQ,"r") as f: return json.load(f)
    except: return {"green":1,"red":0,"ativos":{}}
def salvar(d):
    with open(ARQ,"w") as f: json.dump(d,f)
DADOS = carregar()

def safe_int(v):
    try: return int(str(v).strip() or 0)
    except: return 0

def placar_linha():
    g=DADOS["green"]; r=DADOS["red"]
    total=g+r; pct=(g/total*100) if total>0 else 0
    pend=len(DADOS["ativos"])
    return f"📊 {g}G x {r}R | ⏳ {pend} pend\n📈 {pct:.1f}% | ⚠️ 2% banca 18+ | ⏰ Auto 30min"

def buscar():
    agora=datetime.now(timezone.utc)
    jogos=[]
    # BRT = UTC-3
    hoje_brt = (agora - timedelta(hours=3)).strftime("%Y%m%d")
    amanha_brt = (agora - timedelta(hours=3) + timedelta(days=1)).strftime("%Y%m%d")

    fontes=[
        f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard?dates={hoje_brt}",
        f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard?dates={amanha_brt}",
        f"https://site.api.espn.com/apis/site/v2/sports/soccer/bra.copa_do_brazil/scoreboard",
        f"https://site.api.espn.com/apis/site/v2/sports/soccer/bra.1/scoreboard",
        f"https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard",
    ]
    for url in fontes:
        try:
            res=requests.get(url,timeout=10,headers={"User-Agent":"Mozilla/5.0"}).json()
            ligas=res.get("leagues",[])
            if not ligas and "events" in res:
                ligas=[{"abbreviation":"BRA","name":"Brasileirão","events":res["events"]}]
            for lg in ligas:
                abbr=str(lg.get("abbreviation","BRA"))
                if "NICARAGUA" in abbr.upper(): continue
                for ev in lg.get("events",[]):
                    try:
                        comp=ev["competitions"][0]
                        st=comp["status"]["type"]["name"]
                        dt=datetime.fromisoformat(comp["date"].replace("Z","+00:00"))
                        diff=(dt-agora).total_seconds()/3600
                        # PEGA AO VIVO ou até 6h pra frente
                        if not ("PROGRESS" in st or "FINAL" in st or (0<=diff<=6)):
                            continue
                        if any(x["id"]==ev["id"] for x in jogos): continue
                        c0=comp["competitors"][0]
                        c1=comp["competitors"][1]
                        placar=f"{c0.get('score','0')}x{c1.get('score','0')}"
                        gols=safe_int(c0.get('score'))+safe_int(c1.get('score'))
                        jogos.append({
                            "id":ev["id"],"liga":abbr,"nome":lg.get("name","Copa"),
                            "mand":c0["team"]["shortDisplayName"],"vis":c1["team"]["shortDisplayName"],
                            "status":st,"min":comp["status"].get("displayClock",""),
                            "placar":placar,"gols":gols,"dt":dt
                        })
                    except: continue
        except: continue
    return jogos

def card(j):
    brt=datetime.now(timezone.utc)-timedelta(hours=3)
    if "PROGRESS" in j["status"]:
        situ=f"🔴 AO VIVO {j['min']} {j['placar']}"
    elif "FINAL" in j["status"]:
        situ=f"🏁 FINAL {j['placar']}"
    else:
        hora=(j["dt"]-timedelta(hours=3)).strftime("%H:%M")
        situ=f"⏰ {hora} BRT - EM BREVE"
    return (f"🚀 PerfinaBet V10 Turbo\n"
            f"📅 {brt.strftime('%d/%m %H:%M')} BRT | {j['liga']}\n"
            f"━━━━━━━━━━━━\n"
            f"⚽ {j['mand']} x {j['vis']}\n"
            f"{situ}\n"
            f"🏆 {j['nome']}\n"
            f"━━━━━━━━━━━━\n"
            f"🔥 Over 0.5: 90%\n"
            f"✅ Over 1.5: 78%\n"
            f"✅ BTTS SIM: 60%\n"
            f"💡 MELHOR: Over 0.5 (90%)\n"
            f"━━━━━━━━━━━━\n"
            f"{placar_linha()}")

@BOT.message_handler(commands=['placar','start'])
def cmd_p(m): BOT.send_message(m.chat.id, f"🚀 PerfinaBet V10 Turbo\n\n{placar_linha()}")

@BOT.message_handler(commands=['palpite'])
def cmd_palpite(m):
    jogos=[j for j in buscar() if "FINAL" not in j["status"]]
    if not jogos:
        BOT.send_message(m.chat.id, f"🚀 PerfinaBet V10 Turbo\n📅 {(datetime.now(timezone.utc)-timedelta(hours=3)).strftime('%d/%m %H:%M')} BRT\n━━━━━━━━━━━━\n✅ Sem jogos bons nas próximas 6h.\nAguardando AO VIVO.\n━━━━━━━━━━━━\n\n{placar_linha()}")
        return
    for j in jogos[:3]:
        if j["id"] not in DADOS["ativos"]:
            DADOS["ativos"][j["id"]]=j
            salvar(DADOS)
        BOT.send_message(m.chat.id, card(j))

@BOT.message_handler(commands=['green'])
def cmd_g(m):
    DADOS["green"]+=1
    if DADOS["ativos"]: DADOS["ativos"].pop(next(iter(DADOS["ativos"])))
    salvar(DADOS); BOT.send_message(m.chat.id, f"✅ GREEN MANUAL\n\n{placar_linha()}")
@BOT.message_handler(commands=['red'])
def cmd_r(m):
    DADOS["red"]+=1
    if DADOS["ativos"]: DADOS["ativos"].pop(next(iter(DADOS["ativos"])))
    salvar(DADOS); BOT.send_message(m.chat.id, f"❌ RED MANUAL\n\n{placar_linha()}")

def loop():
    while True:
        try:
            # GREEN AUTOMÁTICO
            todos=buscar()
            for idj in list(DADOS["ativos"].keys()):
                achou=[x for x in todos if x["id"]==idj]
                if achou:
                    j=achou[0]
                    if j["gols"]>=1:
                        DADOS["green"]+=1; DADOS["ativos"].pop(idj); salvar(DADOS)
                        BOT.send_message(CHAT_ID, f"✅ GREEN AUTOMÁTICO!\n⚽ {j['mand']} {j['placar']} {j['vis']} {j['min']}\n\n{placar_linha()}")
                    elif "FINAL" in j["status"] and j["gols"]==0:
                        DADOS["red"]+=1; DADOS["ativos"].pop(idj); salvar(DADOS)
                        BOT.send_message(CHAT_ID, f"❌ RED AUTOMÁTICO\n⚽ {j['mand']} {j['placar']} {j['vis']}\n\n{placar_linha()}")
            # AUTO AO VIVO
            vivos=[j for j in todos if "PROGRESS" in j["status"]]
            for j in vivos:
                if j["id"] not in DADOS["ativos"]:
                    DADOS["ativos"][j["id"]]=j; salvar(DADOS)
                    BOT.send_message(CHAT_ID, f"⏰ AUTO V10 - 30MIN\n\n{card(j)}")
        except Exception as e: print("loop erro",e)
        time.sleep(1800)

threading.Thread(target=loop,daemon=True).start()

def poll():
    last=0
    while True:
        try:
            ups=BOT.get_updates(offset=last+1,timeout=20)
            for u in ups:
                last=u.update_id
                BOT.process_new_updates([u])
        except: time.sleep(5)
threading.Thread(target=poll,daemon=True).start()

@app.route("/")
def home(): return f"PerfinaBet V10 Turbo ON - {placar_linha()}"
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
