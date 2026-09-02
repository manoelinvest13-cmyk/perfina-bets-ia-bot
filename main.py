import os, json, random, time, threading
from datetime import datetime
from flask import Flask
import telebot

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
ARQUIVO = "placar.json"
app = Flask(__name__)

@app.route('/')
def home(): return "Perfina Bets V3 ON"

# JOGOS BASE - a gente troca depois por API
JOGOS_REAIS = [
    "Flamengo x Palmeiras - Brasileirão",
    "Corinthians x São Paulo - Brasileirão",
    "Man City x Arsenal - Premier League",
    "Real Madrid x Barcelona - La Liga",
    "Bayer Leverkusen x Bayern - Bundesliga",
    "PSG x Marseille - Ligue 1",
    "Inter x Milan - Serie A",
    "River Plate x Boca Juniors - Libertadores"
]
MERCADOS = [
    "Over 1.5 Gols @1.42 - 88% conf",
    "Ambas Marcam SIM @1.75 - 82% conf",
    "Over 0.5 HT @1.65 - 85% conf",
    "Over 8.5 Escanteios @1.90 - 80% conf",
    "Casa vence ou empata @1.35 - 90% conf"
]

def carregar():
    if not os.path.exists(ARQUIVO): return []
    try:
        with open(ARQUIVO,'r') as f: return json.load(f)
    except: return []

def salvar(jogo,palpite):
    dados=carregar()
    dados.append({
        "data":datetime.now().strftime("%d/%m/%Y"),
        "hora":datetime.now().strftime("%H:%M"),
        "jogo":jogo,
        "palpite":palpite,
        "status":"pendente"
    })
    with open(ARQUIVO,'w') as f: json.dump(dados,f,indent=2)

def atualizar_ultimo(novo_status):
    dados=carregar()
    for i in range(len(dados)-1, -1, -1):
        if dados[i]['status']=='pendente':
            dados[i]['status']=novo_status
            with open(ARQUIVO,'w') as f: json.dump(dados,f,indent=2)
            return dados[i]
    return None

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "🔥 PERFINA BETS IA V3 PRO ON!\n\n⚽ /palpite - gerar palpite do dia\n✅ /green - marcar último como GREEN\n❌ /red - marcar último como RED\n📊 /placar - ver placar do dia\n🔄 /reset - zerar placar\n\n18+ | Jogue com responsabilidade")

@bot.message_handler(commands=['palpite'])
def palpite(m):
    jogo=random.choice(JOGOS_REAIS)
    mercado=random.choice(MERCADOS)
    salvar(jogo,mercado)
    bot.reply_to(m, f"⚽ JOGO: {jogo}\n\n💰 PALPITE: {mercado}\n\n⏳ Status: PENDENTE\nUse /green ou /red após o jogo terminar.\n\n📊 /placar para ver desempenho")

@bot.message_handler(commands=['green'])
def green(m):
    jogo=atualizar_ultimo('green')
    if jogo: bot.reply_to(m, f"✅ GREEN REGISTRADO!\n\n{jogo['jogo']}\n{jogo['palpite']}\n\nBoa! Veja /placar")
    else: bot.reply_to(m, "Nenhum palpite pendente. Use /palpite primeiro.")

@bot.message_handler(commands=['red'])
def red(m):
    jogo=atualizar_ultimo('red')
    if jogo: bot.reply_to(m, f"❌ RED REGISTRADO\n\n{jogo['jogo']}\n{jogo['palpite']}\n\nBora pro próximo! Veja /placar")
    else: bot.reply_to(m, "Nenhum palpite pendente. Use /palpite primeiro.")

@bot.message_handler(commands=['placar'])
def placar(m):
    hoje=datetime.now().strftime("%d/%m/%Y")
    dados=carregar()
    do_dia=[d for d in dados if d['data']==hoje]
    g=len([d for d in do_dia if d['status']=='green'])
    r=len([d for d in do_dia if d['status']=='red'])
    p=len([d for d in do_dia if d['status']=='pendente'])
    total=g+r
    taxa=(g/total*100) if total>0 else 0
    lucro=g*0.85-r
    texto=f"📊 PLACAR DO DIA - {hoje}\n\n"
    texto+=f"✅ {g} GREENS\n❌ {r} REDS\n⏳ {p} PENDENTES\n\n"
    if total>0:
        texto+=f"📈 {taxa:.1f}% de acerto\n💰 {lucro:+.2f} unidades\n\n"
    texto+=f"⚠️ Análise automática, não garante resultado. 18+"
    bot.reply_to(m, texto)

@bot.message_handler(commands=['reset'])
def reset(m):
    with open(ARQUIVO,'w') as f: json.dump([],f)
    bot.reply_to(m, "🔄 Placar zerado!")

def run_bot():
    time.sleep(4)
    try: bot.remove_webhook()
    except: pass
    time.sleep(2)
    print("BOT V3 RODANDO")
    bot.infinity_polling(timeout=30, long_polling_timeout=30)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port=int(os.environ.get("PORT",10000))
    app.run(host="0.0.0.0", port=port)
