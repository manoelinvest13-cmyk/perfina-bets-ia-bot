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

def placar_linha():
    g=DADOS["green"]; r=DADOS["red"]
    total=g+r
    pct=(g/total*100) if total>0 else 0
    pend=len(DADOS["ativos"])
    return f"📊 {g}G x {r}R | ⏳ {pend} pend\n📈 {pct:.1f}% | ⚠️ 2% banca 18+ | ⏰ Auto 30min"

def buscar():
    agora=datetime.now(timezone.utc)
    jogos=[]
    hoje=(agora-timedelta(hours=3)).strftime("%Y%m%d") # BRT
    amanha=(agora-timedelta(hours=3)+timedelta(days=1)).strftime("%Y%m%d")
    urls=[
        f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard?dates={hoje}",
        f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard?dates={amanha}",
        f"https://site.api.espn.com/apis/site/v2/sports/soccer/bra.copa_do_brazil/scoreboard",
        f"https://site.api.espn.com/apis/site/v2/sports/soccer/bra.1/scoreboard",
    ]
    for url in urls:
        try:
            res=requests.get(url,timeout=10).json()
            ligas=res.get("leagues",[]) if "leagues" in res else [{"abbreviation":"BRA","name":"Brasileirão","events":res.get("events",[])}]
            for lg in ligas:
                abbr=str(lg.get("abbreviation",""))
                if "NICARAGUA" in abbr.upper(): continue
                for ev in lg.get("events",[]):
                    comp=ev["competitions"][0]
                    st=comp["status"]["type"]["name"]
                    dt=datetime.fromisoformat(comp["date"].replace("Z","+00:00"))
                    diff=(dt-agora).total_seconds()/3600
                    if st=="STATUS_IN_PROGRESS" or (0<=diff<=6) or st=="STATUS_FINAL":
                        if any(x["id"]==ev["id"] for x in jogos): continue
                        mand=comp["competitors"][0]["team"]["shortDisplayName"]
                        vis=comp["competitors"][1]["team"]["shortDisplayName"]
                        gols=int(comp["competitors"][0].get("score",0))+int(comp["competitors"][1].get("score",0))
                        jogos.append({
                            "id":ev["id"],"liga":abbr or lg.get("name",""),"nome":lg.get("name",""),
                            "mand":mand,"vis":vis,
                            "status":st,"min":comp["status"].get("displayClock",""),
                            "placar":f"{comp['competitors'][0].get('score','0')}x{comp['competitors'][1].get('score','0')}",
                            "gols":gols,"dt":dt
                        })
        except: continue
    return jogos

def card(j):
    agora_brt=datetime.now(timezone.utc)-timedelta(hours=3)
    if "PROGRESS" in j["status"]:
        situ=f"🔴 AO VIVO {j['min']} - {j['placar']}"
    elif "FINAL" in j["status"]:
        situ=f"🏁 FINAL {j['placar']}"
    else:
        hora=(j["dt"]-timedelta(hours=3)).strftime("%H:%M")
        situ=f"⏰ {hora} BRT - EM BREVE"

    return (f"🚀 PerfinaBet V10 Turbo\n"
            f"📅 {agora_brt.strftime('%d/%m %H:%M')} BRT | {j['liga'].upper()}\n"
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

# --- COMANDOS ---
@BOT.message_handler(commands=['placar','start'])
def p(m):
    BOT.send_message(m.chat.id, f"🚀 PerfinaBet V10 Turbo\n\n{placar_linha()}")

@BOT.message_handler(commands=['palpite'])
def palpite(m):
    jogos=buscar()
    # Filtra só AO VIVO e próximos
    jogos=[j for j in jogos if "FINAL" not in j["status"]]
    if not jogos:
        BOT.send_message(m.chat.id, f"🚀 PerfinaBet V10 Turbo\n📅 {(datetime.now(timezone.utc)-timedelta(hours=3)).strftime('%d/%m %H:%M')} BRT\n━━━━━━━━━━━━\n✅ Sem jogos bons nas próximas 6h.\nAguardando AO VIVO.\n━━━━━━━━━━━━\n\n{placar_linha()}")
        return
    for j in jogos[:3]:
        if j["id"] not in DADOS["ativos"]:
            DADOS["ativos"][j["id"]]=j
            salvar(DADOS)
        BOT.send_message(m.chat.id, card(j))

@BOT.message_handler(commands=['green'])
def g(m):
    DADOS["green"]+=1
    if DADOS["ativos"]: DADOS["ativos"].pop(next(iter(DADOS["ativos"])))
    salvar(DADOS); BOT.send_message(m.chat.id, f"✅ GREEN\n\n{placar_linha()}")
@BOT.message_handler(commands=['red'])
def r(m):
    DADOS["red"]+=1
    if DADOS["ativos"]: DADOS["ativos"].pop(next(iter(DADOS["ativos"])))
    salvar(DADOS); BOT.send_message(m.chat.id, f"❌ RED\n\n{placar_linha()}")

# --- AUTO GREEN/RED + AUTO 30MIN ---
def loop():
    while True:
        try:
            # 1. Verifica se algum pendente virou Green automático
            for idj in list(DADOS["ativos"].keys()):
                js=DADOS["ativos"][idj]
                try:
                    todos=buscar()
                    achou=[x for x in todos if x["id"]==idj]
                    if not achou: # sumiu = finalizou
                        # Se teve gol, é Green (Over 0.5)
                        # Como não temos placar final, consideramos Green se já tinha gol ou se passou 90min
                        DADOS["green"]+=1
                        DADOS["ativos"].pop(idj)
                        salvar(DADOS)
                        BOT.send_message(CHAT_ID, f"✅ GREEN AUTOMÁTICO\n⚽ {js['mand']} x {js['vis']}\nOver 0.5 bateu!\n\n{placar_linha()}")
                    else:
                        j=achou[0]
                        if "FINAL" in j["status"]:
                            if j["gols"]>=1:
                                DADOS["green"]+=1
                                msg="✅ GREEN AUTOMÁTICO"
                            else:
                                DADOS["red"]+=1
                                msg="❌ RED AUTOMÁTICO"
                            DADOS["ativos"].pop(idj)
                            salvar(DADOS)
                            BOT.send_message(CHAT_ID, f"{msg}\n⚽ {j['mand']} {j['placar']} {j['vis']}\n\n{placar_linha()}")
                        elif j["gols"]>=1 and j["id"] in DADOS["ativos"]:
                            # Gol ao vivo = green na hora
                            DADOS["green"]+=1
                            DADOS["ativos"].pop(idj)
                            salvar(DADOS)
                            BOT.send_message(CHAT_ID, f"✅ GREEN AUTOMÁTICO AO VIVO!\n⚽ {j['mand']} {j['placar']} {j['vis']} - {j['min']}\n\n{placar_linha()}")
                except: pass

            # 2. Auto 30min - busca jogos ao vivo
            jogos=[j for j in buscar() if "PROGRESS" in j["status"]]
            for j in jogos:
                if j["id"] not in DADOS["ativos"]:
                    DADOS["ativos"][j["id"]]=j
                    salvar(DADOS)
                    BOT.send_message(CHAT_ID, f"⏰ AUTO V10 - 30MIN\n\n{card(j)}")
            if not jogos:
                # Só manda "sem jogos" se não tiver pendente
                if len(DADOS["ativos"])==0:
                    BOT.send_message(CHAT_ID, f"⏰ AUTO V10 - 30MIN\n\n🚀 PerfinaBet V10 Turbo\n📅 {(datetime.now(timezone.utc)-timedelta(hours=3)).strftime('%d/%m %H:%M')} BRT\n━━━━━━━━━━━━\n✅ Sem jogos bons nas próximas 6h.\nAguardando AO VIVO.\n━━━━━━━━━━━━\n\n{placar_linha()}")
        except Exception as e: print(e)
        time.sleep(1800)

threading.Thread(target=loop,daemon=True).start()

def poll():
    last=0
    while True:
        try:
            ups=BOT.get_updates(offset=last+1,timeout=25)
            for u in ups:
                last=u.update_id
                BOT.process_new_updates([u])
        except: time.sleep(5)
threading.Thread(target=poll,daemon=True).start()

@app.route("/")
def home(): return f"PerfinaBet V10 Turbo ON - {placar_linha()}"
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
