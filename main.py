import os, json, time, threading
from datetime import datetime, timezone, timedelta
import requests
from flask import Flask
import telebot

# --- CONFIG ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BOT = telebot.TeleBot(TOKEN)
app = Flask(__name__)

ARQ_PLACAR = "placar.json"

def liga_boa(nome_liga):
    bloqueia = ["NICARAGUA", "EGYPT", "AMATEUR"]
    nome = str(nome_liga).upper()
    for b in bloqueia:
        if b in nome:
            return False
    return True

def carregar():
    try:
        with open(ARQ_PLACAR, "r") as f:
            return json.load(f)
    except:
        return {"green": 1, "red": 0, "ativos": {}}

def salvar(dados):
    with open(ARQ_PLACAR, "w") as f:
        json.dump(dados, f)

DADOS = carregar()

def get_placar_txt():
    g = DADOS["green"]
    r = DADOS["red"]
    total = g + r
    pct = (g/total*100) if total>0 else 0
    pend = len(DADOS["ativos"])
    return f"📊 {g}G x {r}R | ⏳ {pend} pend\n📈 {pct:.1f}% | ⚠️ 2% banca 18+ | ⏰ Auto 30min"

def buscar_jogos():
    agora = datetime.now(timezone.utc)
    jogos = []
    datas = [agora.strftime("%Y%m%d"), (agora + timedelta(days=1)).strftime("%Y%m%d")]
    for data in datas:
        try:
            url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard?dates={data}"
            res = requests.get(url, timeout=15).json()
            for liga_obj in res.get("leagues", []):
                abbr = liga_obj.get("abbreviation","ALL")
                nome = liga_obj.get("name","")
                if not liga_boa(abbr) and not liga_boa(nome):
                    continue
                for ev in liga_obj.get("events", []):
                    comp = ev["competitions"][0]
                    status = comp["status"]["type"]["name"]
                    dt = datetime.fromisoformat(comp["date"].replace("Z","+00:00"))
                    diff = (dt - agora).total_seconds()/3600
                    if status == "STATUS_IN_PROGRESS" or (0 <= diff <= 5):
                        if any(j["id"] == ev["id"] for j in jogos):
                            continue
                        jogos.append({
                            "id": ev["id"],
                            "liga": abbr,
                            "liga_nome": nome,
                            "mandante": comp["competitors"][0]["team"]["shortDisplayName"],
                            "visitante": comp["competitors"][1]["team"]["shortDisplayName"],
                            "status": status,
                            "minuto": comp["status"].get("displayClock",""),
                            "placar": f"{comp['competitors'][0].get('score','0')}x{comp['competitors'][1].get('score','0')}",
                            "data": dt
                        })
        except:
            continue
    return jogos

def gerar_palpite(jogo):
    ao_vivo = f"{jogo['minuto']} {jogo['placar']}" if "PROGRESS" in jogo['status'] else "EM BREVE"
    return (
        f"🚀 PerfinaBet V10 Turbo\n"
        f"📅 {datetime.now().strftime('%d/%m %H:%M')} BRT | {jogo['liga']}\n"
        f"━━━━━━━━━━━━\n"
        f"🔴 {jogo['status']} {ao_vivo}\n"
        f"⚽ {jogo['mandante']} x {jogo['visitante']}\n"
        f"🏆 {jogo['liga_nome']}\n"
        f"🔥 Over 0.5: 90%\n"
        f"✅ Over 1.5: 78%\n"
        f"✅ BTTS SIM: 60%\n"
        f"💡 MELHOR: Over 0.5 (90%)\n"
        f"━━━━━━━━━━━━\n"
        f"{get_placar_txt()}"
    )

@BOT.message_handler(commands=['palpite'])
def cmd_palpite(m):
    jogos = buscar_jogos()
    if not jogos:
        BOT.send_message(m.chat.id, f"✅ PerfinaBet V10 Turbo - Sem jogos bons nas próximas 5h.\nAguardando AO VIVO.\n\n{get_placar_txt()}")
        return
    for j in jogos[:5]:
        if j["id"] not in DADOS["ativos"]:
            DADOS["ativos"][j["id"]] = j
            salvar(DADOS)
        BOT.send_message(m.chat.id, gerar_palpite(j))

@BOT.message_handler(commands=['placar'])
def cmd_placar(m):
    BOT.send_message(m.chat.id, f"🚀 PerfinaBet V10 Turbo\n\n{get_placar_txt()}")

@BOT.message_handler(commands=['green'])
def cmd_green(m):
    DADOS["green"] += 1
    if DADOS["ativos"]:
        DADOS["ativos"].pop(next(iter(DADOS["ativos"])))
    salvar(DADOS)
    BOT.send_message(m.chat.id, f"✅ GREEN - PerfinaBet V10 Turbo\n\n{get_placar_txt()}")

@BOT.message_handler(commands=['red'])
def cmd_red(m):
    DADOS["red"] += 1
    if DADOS["ativos"]:
        DADOS["ativos"].pop(next(iter(DADOS["ativos"])))
    salvar(DADOS)
    BOT.send_message(m.chat.id, f"❌ RED - PerfinaBet V10 Turbo\n\n{get_placar_txt()}")

def loop_auto():
    while True:
        try:
            jogos = buscar_jogos()
            if jogos:
                for j in jogos:
                    if j["id"] not in DADOS["ativos"] and "PROGRESS" in j["status"]:
                        DADOS["ativos"][j["id"]] = j
                        salvar(DADOS)
                        BOT.send_message(CHAT_ID, f"⏰ AUTO V10 - 30MIN\n\n{gerar_palpite(j)}")
            else:
                BOT.send_message(CHAT_ID, f"⏰ AUTO V10 - 30MIN\n\n🚀 PerfinaBet V10 Turbo\n📅 {datetime.now().strftime('%d/%m %H:%M')} BRT\n━━━━━━━━━━━━\n✅ Sem jogos bons nas próximas 5h.\nAguardando AO VIVO.\n━━━━━━━━━━━━\n\n{get_placar_txt()}")
        except Exception as e:
            print(e)
        time.sleep(1800)

threading.Thread(target=loop_auto, daemon=True).start()

def start_bot():
    last_update = 0
    while True:
        try:
            updates = BOT.get_updates(offset=last_update+1, timeout=20)
            for u in updates:
                last_update = u.update_id
                BOT.process_new_updates([u])
        except:
            time.sleep(5)

threading.Thread(target=start_bot, daemon=True).start()

@app.route("/")
def home():
    return f"PerfinaBet V10 Turbo ON - {get_placar_txt()}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
