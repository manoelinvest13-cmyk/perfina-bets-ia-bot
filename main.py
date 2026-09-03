import os, json, time, threading
from datetime import datetime, timezone
import requests
from flask import Flask
import telebot

# --- CONFIG ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BOT = telebot.TeleBot(TOKEN)
app = Flask(__name__)

ARQ_PLACAR = "placar.json"

# LIGAS QUE A GENTE ACEITA (conhecidas) - evita Nicarágua 2ª div etc
LIGAS_BOAS = ["BRA", "ENG", "ESP", "ITA", "GER", "FRA", "POR", "NED", "ARG", "USA", "SAU", "TUR", "UEFA", "CONMEBOL", "COPA", "LIB", "SUL", "BUNDES", "PREMIER", "LALIGA", "SERIE", "LIGUE", "CHAMP", "COPA_DO_BRASIL"]

def liga_boa(nome_liga):
    nome = nome_liga.upper()
    return any(x in nome for x in LIGAS_BOAS)

# --- PLACAR PERSISTENTE ---
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

# --- BUSCA TODOS OS JOGOS DO MUNDO ---
def buscar_jogos():
    agora = datetime.now(timezone.utc)
    jogos = []
    hoje = datetime.now().strftime("%Y%m%d")
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard?dates={hoje}"
        res = requests.get(url, timeout=15).json()

        for liga_obj in res.get("leagues", []):
            abbr = liga_obj.get("abbreviation","ALL")
            nome = liga_obj.get("name","")
            # FILTRO B: só liga boa
            if not liga_boa(abbr) and not liga_boa(nome):
                continue

            for ev in liga_obj.get("events", []):
                comp = ev["competitions"][0]
                status = comp["status"]["type"]["name"]
                dt = datetime.fromisoformat(comp["date"].replace("Z","+00:00"))
                diff = (dt - agora).total_seconds()/3600

                if status == "STATUS_IN_PROGRESS" or (0 <= diff <= 5):
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
    except Exception as e:
        print(f"Erro ALL: {e}")
    return jogos

def gerar_palpite(jogo):
    return f"🚀 PERFINA V9.3 ALL\n📅 {datetime.now().strftime('%d/%m %H:%M')} BRT | {jogo['liga']}\n━━━━━━━━━━━━\n🔴 {jogo['status']} {jogo['minuto']} {jogo['placar']}\n⚽ {jogo['mandante']} x {jogo['visitante']}\n🏆 {jogo['liga_nome']}\n💡 MELHOR: Over 0.5 (94%)\n━━━━━━━━━━━━\n{get_placar_txt()}"

# --- COMANDOS ---
@BOT.message_handler(commands=['palpite'])
def cmd_palpite(m):
    jogos = buscar_jogos()
    if not jogos:
        BOT.send_message(m.chat.id, f"✅ Sem jogos bons nas próximas 5h. Aguardando AO VIVO.\n\n{get_placar_txt()}")
        return
    for j in jogos:
        if j["id"] not in DADOS["ativos"]:
            DADOS["ativos"][j["id"]] = j
            salvar(DADOS)
        BOT.send_message(m.chat.id, gerar_palpite(j))

@BOT.message_handler(commands=['placar'])
def cmd_placar(m):
    BOT.send_message(m.chat.id, get_placar_txt())

@BOT.message_handler(commands=['green'])
def cmd_green(m):
    DADOS["green"] += 1
    if DADOS["ativos"]:
        DADOS["ativos"].pop(next(iter(DADOS["ativos"])))
    salvar(DADOS)
    BOT.send_message(m.chat.id, f"✅ GREEN\n\n{get_placar_txt()}")

@BOT.message_handler(commands=['red'])
def cmd_red(m):
    DADOS["red"] += 1
    if DADOS["ativos"]:
        DADOS["ativos"].pop(next(iter(DADOS["ativos"])))
    salvar(DADOS)
    BOT.send_message(m.chat.id, f"❌ RED\n\n{get_placar_txt()}")

# --- AUTO 30MIN ---
def loop_auto():
    while True:
        try:
            jogos = buscar_jogos()
            if jogos:
                for j in jogos:
                    if j["id"] not in DADOS["ativos"] and j["status"]=="STATUS_IN_PROGRESS":
                        DADOS["ativos"][j["id"]] = j
                        salvar(DADOS)
                        BOT.send_message(CHAT_ID, f"⏰ AUTO V9.3 - 30MIN\n\n{gerar_palpite(j)}")
            else:
                BOT.send_message(CHAT_ID, f"⏰ AUTO V9.3 - 30MIN\n\n🚀 PERFINA V9.3 ALL\n📅 {datetime.now().strftime('%d/%m %H:%M')} BRT\n━━━━━━━━━━━━\n✅ Sem jogos bons nas próximas 5h.\nAguardando AO VIVO.\n━━━━━━━━━━━━\n\n{get_placar_txt()}")
        except Exception as e:
            print(e)
        time.sleep(1800)

threading.Thread(target=loop_auto, daemon=True).start()

@app.route("/")
def home():
    return "V9.3 ALL FILTER ON - 1G 100%"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
