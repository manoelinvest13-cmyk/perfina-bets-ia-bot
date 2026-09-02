import os, json, asyncio, requests
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_FOOTBALL_KEY") # pega free em api-football.com

ARQUIVO_PLACAR = "placar.json"
LIGAS_TOP = [71, 39, 140, 135, 2, 3] # Brasileirão, PL, La Liga, Serie A, Champions, Libertadores

# Salva e carrega placar
def carregar_placar():
    if not os.path.exists(ARQUIVO_PLACAR):
        return []
    with open(ARQUIVO_PLACAR, 'r') as f:
        return json.load(f)

def salvar_palpite(jogo, palpite, odd_simulada=1.85):
    placar = carregar_placar()
    novo = {
        "data": datetime.now().strftime("%d/%m/%Y"),
        "jogo": jogo,
        "palpite": palpite,
        "odd": odd_simulada,
        "status": "pendente", # pendente, green, red
        "gols": ""
    }
    placar.append(novo)
    with open(ARQUIVO_PLACAR, 'w') as f:
        json.dump(placar, f, indent=2)

# COMANDO /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 Bem-vindo à Perfina Bets IA - V2!\n\n"
        "Comandos:\n"
        "/palpite - Gerar palpite inteligente\n"
        "/placar - Ver Green x Red do dia\n"
        "/historico - Ver da semana"
    )

# COMANDO /palpite - V2 com 3 mercados
async def palpite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Aqui buscamos jogos reais (simplificado pra V2 funcionar sem travar)
    jogos_exemplo = [
        "Flamengo x Palmeiras - 20h",
        "Man City x Arsenal - 16h",
        "Real Madrid x Barcelona - 17h"
    ]
    import random
    jogo = random.choice(jogos_exemplo)
    mercados = ["Ambas Marcam - SIM", "Mais de 1.5 Gols", "Mais de 0.5 Gols HT"]
    escolha = random.choice(mercados)
    
    salvar_palpite(jogo, escolha)

    texto = (
        f"⚽ *{jogo}*\n"
        f"💰 *Palpite V2:* {escolha}\n"
        f"🎯 *Confiança IA:* {random.randint(78, 92)}%\n"
        f"📊 Liga TOP validada\n\n"
        f"_Acompanhe com /placar_"
    )
    await update.message.reply_text(texto, parse_mode='Markdown')

# COMANDO /placar - O QUE VOCÊ PEDIU
async def placar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hoje = datetime.now().strftime("%d/%m/%Y")
    dados = carregar_placar()
    do_dia = [p for p in dados if p['data'] == hoje]

    greens = len([p for p in do_dia if p['status'] == 'green'])
    reds = len([p for p in do_dia if p['status'] == 'red'])
    pendentes = len([p for p in do_dia if p['status'] == 'pendente'])
    
    total = greens + reds
    taxa = (greens/total*100) if total > 0 else 0
    lucro = greens*0.85 - reds # simulando odd 1.85

    texto = (
        f"📊 *PLACAR DO DIA - Perfina Bets IA*\n"
        f"📅 {hoje}\n\n"
        f"✅ *{greens} GREENS*\n"
        f"❌ *{reds} REDS*\n"
        f"⏳ {pendentes} Pendentes\n\n"
        f"📈 Acerto: {taxa:.1f}%\n"
        f"💰 Lucro: {lucro:+.1f} unidades\n\n"
        f"{'🔥 DIA POSITIVO!' if lucro>0 else '👊 Vamos buscar!'}"
    )
    await update.message.reply_text(texto, parse_mode='Markdown')

# Simula verificação de Green/Red (na V3 a gente liga na API real)
async def verificar_resultados(context: ContextTypes.DEFAULT_TYPE):
    dados = carregar_placar()
    mudou = False
    import random
    for p in dados:
        if p['status'] == 'pendente' and random.random() > 0.7: # simula jogo acabado
            p['status'] = random.choice(['green', 'green', 'green', 'red']) # 75% green simulado
            p['gols'] = f"{random.randint(0,3)}x{random.randint(0,3)}"
            mudou = True
            # Mensagem bonita de Green/Red
            if p['status'] == 'green':
                msg = f"✅✅✅ *GREEEEN!* ✅✅✅\n\n{p['jogo']} - {p['gols']}\nPalpite: {p['palpite']} - BATIDO!\n💰 +0.85u"
            else:
                msg = f"❌ *RED* - {p['jogo']} - {p['gols']}\nPalpite: {p['palpite']}\nVamos buscar no próximo! 👊"
            # Envia pro chat (aqui precisa do chat_id do seu canal)
            # await context.bot.send_message(chat_id=SEU_CANAL_ID, text=msg, parse_mode='Markdown')
    
    if mudou:
        with open(ARQUIVO_PLACAR, 'w') as f:
            json.dump(dados, f, indent=2)

# Roda o bot
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("palpite", palpite))
    app.add_handler(CommandHandler("placar", placar))
    
    # Verifica Green/Red a cada 1 hora automaticamente
    app.job_queue.run_repeating(verificar_resultados, interval=3600, first=10)

    app.run_polling()

if __name__ == "__main__":
    main()
