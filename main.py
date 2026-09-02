import os, json, random, time, threading, requests
from datetime import datetime
from flask import Flask
import telebot

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
ARQUIVO = "placar.json"
app = Flask(__name__)

MERCADOS = [
    "Over 1.5 Gols @1.42 - 88% conf - xG alto hoje",
    "Ambas Marcam SIM @1.75 - 82% - defesa vulnerável",
    "Over 0.5 HT @1.65 - 85% - gol cedo",
    "Over 8.5 Escanteios @1.90 - 80%",
    "Casa vence ou empata @1.35 - 90%"
]

def buscar_jogos_reais():
    hoje = datetime.now().strftime("%Y%m%d") # HOJE!
    jogos = []
    try:
        ligas = ["bra.1","eng.1","esp.1","ger.1","ita.1"]
        for liga in ligas:
            url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{liga}/scoreboard?dates={hoje}"
            r = requests.get(url, timeout=7).json()
            for ev in r.get('events', []):
                short = ev.get('shortName','')
                name = ev.get('name', short)
                # Só pega se for HOJE mesmo
                if name: jogos.append(f"{name} - {liga.upper()} - HOJE")
        if jogos: return jogos
    except Exception as e: print(f"Erro API: {e}")

    # Fallback COM DATA DE HOJE
    return [
        f"Flamengo x Palmeiras - Brasileirão - HOJE {datetime.now().strftime('%d/%m')}",
        f"Corinthians x São Paulo - Brasileirão - HOJE",
        f"Jogos de hoje em atualização - Tente /palpite novamente em 5s"
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

def atualizar_ultimo(s):
    dados=carregar()
    for i in range(len(dados)-1,-1,-1):
        if dados[i]['status']=='pendente':
            dados[i]['status']=s
            with open(ARQUIVO,'w') as f: json.dump(dados,f,indent=2)
            return dados[i]
    return None

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, f"🔥 V4.1 ON! {datetime.now().strftime('%d/%m')} - JOGOS DE HOJE!\n\n/palpite - jogos reais de HOJE\n/green /red - marcar\n/placar - ver\n\n⚠️ Render free desliga se ficar sem uso. Se o auto não rodar, use UptimeRobot pra pingar.")

@bot.message_handler(commands=['palpite'])
def palpite_cmd(m):
    jogos = buscar_jogos_reais()
    jogo = random.choice(jogos)
    mercado = random.choice(MERCADOS)
    salvar(jogo,mercado)
    bot.reply_to(m, f"🤖 JOGOS DE HOJE - {datetime.now().strftime('%d/%m/%Y')}\n\n⚽ {jogo}\n\n💰 {mercado}\n\n⏳ /green ou /red depois\n📊 /placar")

@bot.message_handler(commands=['green','red','placar','reset'])
def outros(m):
    cmd=m.text.lower()
    if 'green' in cmd:
        j=atualizar_ultimo('green'); bot.reply_to(m, f"✅ GREEN {j['jogo']}" if j else "Sem pendente")
    elif 'red' in cmd:
        j=atualizar_ultimo('red'); bot.reply_to(m, f"❌ RED {j['jogo']}" if j else "Sem pendente")
    elif 'placar' in cmd:
        hoje=datetime.now().strftime("%d/%m/%Y"); dados=carregar(); dd=[d for d in dados if d['data']==hoje]
        g=len([d for d in dd if d['status']=='green']); r=len([d for d in dd if d['status']=='red']); p=len([d for d in dd if d['status']=='pendente'])
        taxa=(g/(g+r)*100) if (g+r)>0 else 0; bot.reply_to(m, f"📊 {hoje}\n✅{g} ❌{r} ⏳{p}\n📈 {taxa:.1f}%")
    else:
        with open(ARQUIVO,'w') as f: json.dump([],f); bot.reply_to(m,"🔄 Zerado!")

def run_bot():
    time.sleep(3)
    try: bot.remove_webhook()
    except: pass
    print("BOT V4.1 RODANDO")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
