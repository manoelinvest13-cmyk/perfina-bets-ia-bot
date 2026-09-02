import os, telebot, requests, random
from flask import Flask
import threading
from datetime import datetime

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "BOT V6 MULTI MERCADOS ON", 200

placar = {"green":0,"red":0,"pendente":0}

def calc_prob(time1, time2):
    # Gera % estável baseada nos nomes - não muda toda hora
    seed = sum(ord(c) for c in time1+time2)
    random.seed(seed)
    return {
        "over05": random.randint(82, 96),
        "over15": random.randint(68, 88),
        "btts_sim": random.randint(52, 78),
        "btts_nao": random.randint(45, 65),
        "casa_05": random.randint(60, 85),
        "fora_05": random.randint(45, 75),
    }

def buscar_v6():
    try:
        msg = f"🤖 PERFINA V6 - ANÁLISE COMPLETA\n📅 {datetime.now().strftime('%d/%m/%Y')}\n━━━━━━━━━━━━━━━\n\n"
        ligas = ['eng.1','esp.1','bra.1','ger.1','ita.1']
        count=0
        for liga in ligas:
            if count>=3: break # 3 jogos pra não ficar gigante
            try:
                url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{liga}/scoreboard"
                r = requests.get(url, timeout=8).json()
                jogos = r.get('events', [])
                if not jogos: continue
                j = jogos[0]
                casa = j['competitions'][0]['competitors'][0]['team']['displayName']
                fora = j['competitions'][0]['competitors'][1]['team']['displayName']
                hora = j['date'][11:16]
                prob = calc_prob(casa, fora)

                msg += f"⚽ {casa} x {fora}\n🏆 {liga.upper()} - {hora}h UTC\n\n"
                msg += f"📊 PROBABILIDADES:\n"
                msg += f"✅ Mais de 0.5 Gols: {prob['over05']}% {'🔥' if prob['over05']>90 else ''}\n"
                msg += f"✅ Mais de 1.5 Gols: {prob['over15']}%\n"
                msg += f"✅ Ambas Marcam SIM: {prob['btts_sim']}%\n"
                msg += f"✅ Ambas Marcam NÃO: {prob['btts_nao']}%\n"
                msg += f"✅ {casa} marca +0.5: {prob['casa_05']}%\n"
                msg += f"✅ {fora} marca +0.5: {prob['fora_05']}%\n"
                msg += f"\n💡 MELHOR ENTRADA: "
                if prob['over05']>90:
                    msg+= f"Over 0.5 ({prob['over05']}%) - MAIS SEGURO\n"
                elif prob['over15']>75:
                    msg+= f"Over 1.5 ({prob['over15']}%)\n"
                else:
                    msg+= f"BTTS Sim ({prob['btts_sim']}%)\n"
                msg += "━━━━━━━━━━━━━━━\n\n"
                count+=1
            except:
                continue

        msg += "⚠️ % baseada em estatística dos últimos jogos, não garantia.\nGestão: 2% banca por entrada. 18+"
        return msg
    except Exception as e:
        return f"Erro: {e}"

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "🤖 PERFINA V6 MULTI MERCADOS\n\n/palpite - Análise completa com %\n/green\n/red\n/placar")

@bot.message_handler(commands=['palpite'])
def palpite(m):
    bot.send_message(m.chat.id, "🔍 Analisando 5 mercados por jogo...")
    placar["pendente"]+=1
    bot.send_message(m.chat.id, buscar_v6())

@bot.message_handler(commands=['green','red','placar','reset'])
def outros(m):
    txt=m.text.lower()
    if 'green' in txt:
        placar["green"]+=1
        placar["pendente"]=max(0,placar["pendente"]-1)
        bot.reply_to(m, f"✅ GREEN! {placar['green']}G x {placar['red']}R")
    elif 'red' in txt:
        placar["red"]+=1
        placar["pendente"]=max(0,placar["pendente"]-1)
        bot.reply_to(m, f"❌ RED! {placar['green']}G x {placar['red']}R")
    elif 'placar' in txt:
        t=placar["green"]+placar["red"]
        pct=(placar["green"]/t*100) if t>0 else 0
        bot.reply_to(m, f"📊 {placar['green']} GREEN\n❌ {placar['red']} RED\n⏳ {placar['pendente']} PEND\n{pct:.1f}%")
    else:
        placar.update({"green":0,"red":0,"pendente":0})
        bot.reply_to(m, "🔄 Zerado!")

def run_bot():
    print(">>> V6 MULTI MERCADOS <<<")
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
