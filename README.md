# Perfina Bets IA Bot

Bot do Telegram em Python que consulta jogos reais de futebol do dia no
TheSportsDB e gera palpites automáticos.

## Deploy no Render

1. Crie um serviço **Background Worker** usando este repositório.
2. O `render.yaml` já define os comandos de instalação e inicialização.
3. Adicione a variável secreta `TELEGRAM_BOT_TOKEN` no Render.

## Comandos

- `/start`
- `/palpite`
- `/jogos`
- `/ajuda`
- `/status`

As análises são informativas e não garantem resultados. Jogue com
responsabilidade e apenas se isso for legal na sua região.