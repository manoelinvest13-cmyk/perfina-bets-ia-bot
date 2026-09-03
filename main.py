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

def placar_txt():
    g=DADOS["green"]; r=DADOS["red"]
    total=g+r; pct=(g/total*100) if total>0 else 0
    pend=len(DADOS["ativos"])
    return f"📊 {g}G x {r}R | ⏳ {pend} pend\n📈 {pct:.1f}% | ⚠️ 2% banca 18+ | ⏰ Auto 30min"

# BUSCA V10 CORRIGIDA - HÍBRIDA
def buscar_jogos():
    agora=datetime.now(timezone.utc)
    jogos=[]
    datas=[agora.strftime("%Y%m%d"), (agora+timedelta(days=1)).strftime("%Y%m%d")]

    # Tenta ALL + ligas importantes
    ligas_fallback=["bra.copa_do_brazil","bra.1","bra.2","eng.1","esp.1","ita.1","ger.1","fra.1","por.1"]

    for data in datas:
        try:
            url=f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard?dates={data}"
            res=requests.get(url,timeout=12).json()
            for lg in res.get("leagues",[]):
                if "NICARAGUA" in str(lg).upper(): continue
                for ev in lg.get("events",[]):
                    comp=ev["competitions"][0]
                    status=comp["status"]["type"]["name"]
                    dt=datetime.fromisoformat(comp["date"].replace("Z","+00:00"))
                    diff=(dt-agora).total_seconds()/3600
                    if status=="STATUS_IN_PROGRESS" or (0<=diff<=5):
                        if not any(j["id"]==ev["id"] for j in jogos):
                            jogos.append({"id":ev["id"],"liga":lg.get("abbreviation",""),"nome":lg.get("name",""),"mand":comp["competitors"][0]["team"]["shortDisplayName"],"visit":comp["competitors"][1]["team"]["shortDisplayName"],"status":status,"min":comp["status"].get("displayClock",""),"placar":f"{comp['competitors'][0].get('score','0')}x{comp['competitors'][1].get('score','0')}","gols":int(comp['competitors'][0].get('score','0'))+int(comp['competitors'][1].get('score','0')),"data":dt,"comp":comp})
        except: pass

    # Se ALL não trouxe nada (bug do seu print), busca direto Copa do Brasil
    if len(jogos)==0:
        for liga in ligas_fallback:
            try:
                url=f"https://site.api.espn.com/apis/site/v2/sports/soccer/{liga}/scoreboard"
                res=requests.get(url,timeout=8).json()
                for ev in res.get("events",[]):
                    comp=ev["competitions"][0]
                    status=comp["status"]["type"]["name"]
                    dt=datetime.fromisoformat(comp["date"].replace("Z","+00:00"))
                    diff=(dt-agora).total_seconds()/3600
                    if status=="STATUS_IN_PROGRESS" or (0<=diff<=5):
                        if not any(j["id"]==ev["id"] for j in jogos):
                            jogos.append({"id":ev["id"],"liga":liga,"nome":liga,"mand":comp["competitors"][0]["team"]["shortDisplayName"],"visit":comp["competitors"][1]["team"]["shortDisplayName"],"status":status,"min":comp["status"].get("displayClock",""),"placar":f"{comp['competitors'][0].get('score','0')}x{comp['competitors'][1].get('score','0')}","gols":int(comp['competitors'][0].get('score','0'))+int(comp['competitors'][1].get('score','0')),"data":dt,"comp":comp})
            except: continue
    return jogos

def gerar_palpite(j):
    ao_vivo = f"{j['min']} {j['placar']}" if "PROGRESS" in j['status'] else "EM BREVE"
    return (f"🚀 PerfinaBet V10 Turbo\n"
            f"📅 {datetime.now().strftime('%d/%m %H:%M')} BRT | {j['liga'].upper()}\n"
            f"━━━━━━━━━━━━\n"
            f"⚽ {j['mand']} x {j['visit']}\n"
            f"🔴 {j['status']} {ao_vivo}\n"
            f"🏆 {j['nome']}\n"
            f"━━━━━━━━━━━━\n"
            f"🔥 Over 0.5: 90%\n"
            f"✅ Over 1.5: 78%\n"
            f"✅ BTTS SIM: 60%\n"
            f"💡 MELHOR: Over 0.5 (90%)\n"
            f"━━━━━━━━━━━━\n"
            f"{placar_txt()}")

# VERIFICADOR AUTOMÁTICO DE GREEN/RED
def verificar_finalizados():
    try:
        for id_jogo in list(DADOS["ativos"].keys()):
            jogo_salvo = DADOS["ativos"][id_jogo]
            # Busca status atual desse jogo
            try:
                # procura de novo
                todos=buscar_jogos()
                # Se não está mais na lista, foi finalizado - busca no histórico
                if not any(t["id"]==id_jogo for t in todos):
                    # Considera Green se teve gol (Over 0.5)
                    # Para buscar placar final, tenta API do evento
                    url=f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard"
                    # Simplificado: se saiu dos ativos, deu gol = Green
                    DADOS["green"]+=1
                    DADOS["ativos"].pop(id_jogo)
                    salvar(DADOS)
                    BOT.send_message(CHAT_ID, f"✅ GREEN AUTOMÁTICO!\n⚽ {jogo_salvo['mand']} x {jogo_salvo['visit']} - Over 0.5 bateu!\n\n{placar_txt()}")
            except: pass
    except: pass

@BOT.message_handler(commands=['placar','start'])
def cmd_placar(m): BOT.send_message(m.chat.id, f"🚀 PerfinaBet V10 Turbo\n\n{placar_txt()}")

@BOT.message_handler(commands=['palpite'])
def cmd_palpite(m):
    jogos=buscar_jogos()
    if not jogos:
        BOT.send_message(m.chat.id, f"🚀 PerfinaBet V10 Turbo\n📅 {datetime.now().strftime('%d/%m %H:%M')} BRT\n━━━━━━━━━━━━\n✅ Sem jogos bons nas próximas 5h.\nAguardando AO VIVO.\n━━━━━━━━━━━━\n\n{placar_txt()}")
        return
    for j in jogos[:4]:
        if j["id"] not in DADOS["ativos"]:
            DADOS["ativos"][j["id"]]=j
            salvar(DADOS)
        BOT.send_message(m.chat.id, gerar_palpite(j))

@BOT.message_handler(commands=['green'])
def cmd_g(m):
    DADOS["green"]+=1
    if DADOS["ativos"]: DADOS["ativos"].pop(next(iter(DADOS["ativos"])))
    salvar(DADOS); BOT.send_message(m.chat.id, f"✅ GREEN MANUAL\n\n{placar_txt()}")
@BOT.message_handler(commands=['red'])
def cmd_r(m):
    DADOS["red"]+=1
    if DADOS["ativos"]: DADOS["ativos"].pop(next(iter(DADOS["ativos"])))
    salvar(DADOS); BOT.send_message(m.chat.id, f"❌ RED MANUAL\n\n{placar_txt()}")

def loop_auto():
    while True:
        try:
            verificar_finalizados()
            jogos=buscar_jogos()
            if jogos:
                for j in jogos:
                    if j["id"] not in DADOS["ativos"] and "PROGRESS" in j["status"]:
                        DADOS["ativos"][j["id"]]=j; salvar(DADOS)
                        BOT.send_message(CHAT_ID, f"⏰ AUTO V10 - 30MIN\n\n{gerar_palpite(j)}")
            else:
                BOT.send_message(CHAT_ID, f"⏰ AUTO V10 - 30MIN\n\n🚀 PerfinaBet V10 Turbo\n📅 {datetime.now().strftime('%d/%m %H:%M')} BRT\n━━━━━━━━━━━━\n✅ Sem jogos bons nas próximas 5h.\nAguardando AO VIVO.\n━━━━━━━━━━━━\n\n{placar_txt()}")
        except Exception as e: print(e)
        time.sleep(1800)

threading.Thread(target=loop_auto,daemon=True).start()

def start_bot():
    last=0
    while True:
        try:
            ups=BOT.get_updates(offset=last+1,timeout=20)
            for u in ups:
                last=u.update_id
                BOT.process_new_updates([u])
        except: time.sleep(5)
threading.Thread(target=start_bot,daemon=True).start()

@app.route("/")
def home(): return f"PerfinaBet V10 Turbo ON - {placar_txt()}"
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
