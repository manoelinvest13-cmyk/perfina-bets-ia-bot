# Perfina Bets IA PRO

Bot do Telegram em Python para buscar jogos reais de futebol do dia e gerar
palpites automáticos usando dados do TheSportsDB.

## Iniciar

O token do BotFather deve estar salvo no segredo `TELEGRAM_BOT_TOKEN`.

```bash
python bot/bot.py
```

## Comandos

- `/start` — iniciar
- `/ajuda` — mostrar os comandos
- `/palpite` — buscar até 10 jogos reais do dia e gerar palpites
- `/jogos` — atalho para `/palpite`
- `/status` — confirmar que o bot está online

O bot usa a API pública do TheSportsDB e aplica uma regra inicial transparente:
competições de maior destaque recebem a sugestão “Mais de 1.5 Gols”; as demais,
“Ambas Marcam”. Isso é uma análise automática, não uma garantia de resultado e
não inclui odds reais.
