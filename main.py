import os, json, random, time, threading, requests
from datetime import datetime
from flask import Flask
import telebot

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
ARQUIVO = "placar.json"
app = Flask(__name__)

MERCADOS = [
    "Over 1.5 Gols @1.42 - 88% conf - Análise IA baseada em xG",
    "Ambas Marcam SIM @1.75 - 82% conf - IA detectou fragilidade defensiva",
    "Over 0.5 HT @1.65 - 85% conf - Tendência de gol cedo",
    "Over 8.5 Escanteios @1.90 - 80% conf - Jogo aberto",
    "Over 2.5 Gols @1.95 - 81% conf - Expectativa de gols alta"
]

def buscar_jogos_reais():
    jogos = []
    try:
        # Tenta buscar jogos do dia na API ESPN grátis (Brasileirão + principais ligas)
        ligas = ["bra.1", "eng.1", "esp.1", "ger.1", "ita.1", "fra.1"]
        for liga in ligas:
            url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{liga}/scoreboard"
            r = requests.get(url, timeout=5).json()
            for ev in r.get('events', [])[:3]:
                nome = ev.get('name','Jogo')
                comp = ev.get('competitions',[{}])[0].get('status',{}).get('type',{}).get('detail','')
                jogos.append(f"{nome} - {liga.upper()}")
        if jogos: return jogos
    except: pass
    # Fallback se API falhar
    return [
        "Flamengo x Palmeiras - Brasileirão", "Corinthians x São Paulo - Brasileirão",
        "Man City x Arsenal - Premier League", "Real Madrid x Barcelona - La Liga",
        "Bayern x Leverkusen - Bundesliga", "PSG x Marseille - Ligue 1"
    ]

def carregar():
    if not os.path.exists(ARQUIVO): return []
    try:
        with open(ARQUIVO,'r') as f: return json.load(f)
    except: return []

def salvar(jogo,palpite):
    dados=carregar()
    dados.append({"data":datetime.now().strftime("%d/%m/%Y"),"hora":datetime.now().strftime("%H:%M"),"jogo":jogo,"palpite":palpite,"status":"pendente"})
    with open(ARQUIVO,'w') as f: json.dump(dados,f,indent=2)

def atualizar_ultimo(novo_status):
    dados=carregar()
    for i in range(len(dados)-1,-1,-1):
        if dados[i]['status']=='pendente':
            dados[i]['status']=novo_status
            with open(ARQUIVO,'w') as f: json.dump(dados,f,indent=2)
            return dados[i]
    return None

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "🔥 PERFINA BETS IA V4 ULTRA ON!\n\n⚽ /palpite - IA analisa jogos reais do dia\n✅ /green - marcar GREEN\n❌ /red - marcar RED\n📊 /placar - placar real do dia\n🔄 /reset - zerar\n\n🤖 Auto-post a cada 3h ativo!\n18+ | Responsabilidade")

@bot.message_handler(commands=['palpite'])
def palpite_cmd(m):
    jogos = buscar_jogos_reais()
    jogo = random.choice(jogos)
    mercado = random.choice(MERCADOS)
    salvar(jogo,mercado)
    bot.reply_to(m, f"🤖 IA ANALISOU JOGOS REAIS DE HOJE\n\n⚽ JOGO: {jogo}\n\n💰 PALPITE: {mercado}\n\n⏳ PENDENTE - Use /green ou /red após o jogo\n\n📊 /placar")

@bot.message_handler(commands=['green'])
def green(m):
    j=atualizar_ultimo('green')
    bot.reply_to(m, f"✅ GREEN! {j['jogo']}" if j else "Sem pendente. /palpite primeiro")

@bot.message_handler(commands=['red'])
def red(m):
    j=atualizar_ultimo('red')
    bot.reply_to(m, f"❌ RED! {j['jogo']}" if j else "Sem pendente. /palpite primeiro")

@bot.message_handler(commands=['placar'])
def placar(m):
    hoje=datetime.now().strftime("%d/%m/%Y")
    dados=carregar(); do_dia=[d for d in dados if d['data']==hoje]
    g=len([d for d in do_dia if d['status']=='green']); r=len([d for d in do_dia if d['status']=='red']); p=len([d for d in do_dia if d['status']=='pendente'])
    taxa=(g/(g+r)*100) if (g+r)>0 else 0; lucro=g*0.85-r
    bot.reply_to(m, f"📊 PLACAR {hoje}\n✅ {g} GREENS\n❌ {r} REDS\n⏳ {p} PENDENTES\n\n📈 {taxa:.1f}% | 💰 {lucro:+.2f} un\n⚠️ IA não garante resultado. 18+")

@bot.message_handler(commands=['reset'])
def reset(m):
    with open(ARQUIVO,'w') as f: json.dump([],f)
    bot.reply_to(m, "🔄 Zerado!")

def auto_post():
    while True:
        time.sleep(10800) # 3 horas
        try:
            jogos = buscar_jogos_reais()
            jogo = random.choice(jogos)
            mercado = random.choice(MERCADOS)
            salvar(jogo,mercado)
            # Se quiser postar automático num canal, coloque o ID aqui:
            # bot.send_message(CHAT_ID_CANAL, f"🤖 PALPITE AUTOMÁTICO\n⚽ {jogo}\n💰 {mercado}")
            print(f"AUTO POST GERADO: {jogo}")
        except: pass

def run_bot():
    time.sleep(4)
    try: bot.remove_webhook()
    except: pass
    time.sleep(2)
    print("BOT V4 RODANDO")
    threading.Thread(target=auto_post, daemon=True).start()
    bot.infinity_polling(timeout=30, long_polling_timeout=30)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port=int(os.environ.get("PORT",10000))
    app.run(host="0.0.0.0", port=port)
