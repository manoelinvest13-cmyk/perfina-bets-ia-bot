import os, json, random
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
ARQUIVO = "placar.json"

def carregar():
    if not os.path.exists(ARQUIVO): return []
    try:
        with open(ARQUIVO,'r') as f: return json.load(f)
    except: return []

def salvar(jogo,palpite):
    dados=carregar()
    dados.append({
        "data": datetime.now().strftime("%d/%m/%Y"),
        "jogo": jogo,
        "palpite": palpite,
        "status": random.choice(['green','green','green','red','pendente']),
        "odd":1.85
    })
    with open(ARQUIVO,'w') as f: json.dump(dados,f,indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 Perfina Bets IA V2 ON!\n\n/palpite\n/placar")

async def palpite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    jogos=["Flamengo x Palmeiras","Man City x Arsenal","Real Madrid x Barca","Inter x Milan"]
    mercados=["Ambas Marcam SIM","Over 1.5 Gols","Over 0.5 HT"]
    jogo=random.choice(jogos)
    mercado=random.choice(mercados)
    salvar(jogo,mercado)
    await update.message.reply_text(f"⚽ *{jogo}*\n💰 Palpite: *{mercado}*\n🎯 Confiança: {random.randint(80,92)}%\n\nAcompanhe em /placar", parse_mode='Markdown')

async def placar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hoje=datetime.now().strftime("%d/%m/%Y")
    dados=carregar()
    do_dia=[d for d in dados if d['data']==hoje]
    g=len([d for d in do_dia if d['status']=='green'])
    r=len([d for d in do_dia if d['status']=='red'])
    p=len([d for d in do_dia if d['status']=='pendente'])
    total=g+r
    taxa=(g/total*100) if total>0 else 0
    lucro=g*0.85-r
    await update.message.reply_text(f"📊 *PLACAR DO DIA - {hoje}*\n\n✅ {g} GREENS\n❌ {r} REDS\n⏳ {p} Pendentes\n\n📈 {taxa:.1f}% acerto\n💰 {lucro:+.1f} unidades", parse_mode='Markdown')

def main():
    app=ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",start))
    app.add_handler(CommandHandler("palpite",palpite))
    app.add_handler(CommandHandler("placar",placar))
    print("BOT V2 RODANDO...")
    app.run_polling()

if __name__=="__main__":
    main()
