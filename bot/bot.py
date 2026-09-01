"""Perfina Bets IA PRO — Telegram bot with live football fixtures."""

from __future__ import annotations

import logging
import os
from datetime import datetime
from html import escape
from typing import Any

import requests
import telebot
from telebot import TeleBot


BOT_NAME = "Perfina Bets IA PRO"
TOKEN_ENV = "TELEGRAM_BOT_TOKEN"
LEGACY_TOKEN_ENV = "TELEGRAM_TOKEN"
SPORTS_DB_URL = "https://www.thesportsdb.com/api/v1/json/3/eventsday.php"
MAX_MATCHES = 10

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(BOT_NAME)
logging.getLogger("urllib3").setLevel(logging.WARNING)
telebot.logger.setLevel(logging.WARNING)


def buscar_jogos_hoje() -> list[dict[str, Any]]:
    """Fetch today's football events from TheSportsDB."""
    hoje = datetime.now().strftime("%Y-%m-%d")
    response = requests.get(
        SPORTS_DB_URL,
        params={"d": hoje, "s": "Soccer"},
        timeout=15,
    )
    response.raise_for_status()
    events = response.json().get("events") or []
    return events[:MAX_MATCHES]


def analisar_jogo(jogo: dict[str, Any]) -> tuple[str, str, float, bool, str, str]:
    """Create a transparent first-pass suggestion from the competition name."""
    casa = str(jogo.get("strHomeTeam") or "Time da casa")
    fora = str(jogo.get("strAwayTeam") or "Time visitante")
    liga = str(jogo.get("strLeague") or "Competição não informada")
    raw_time = str(jogo.get("strTime") or "")
    hora = raw_time[:5] if len(raw_time) >= 5 else "horário a confirmar"

    ligas_gols = {
        "Premier League",
        "La Liga",
        "Bundesliga",
        "Brasileirão",
        "Champions League",
    }
    if liga in ligas_gols:
        return f"{casa} x {fora}", "Mais de 1.5 Gols", 8.0, True, liga, hora
    return f"{casa} x {fora}", "Ambas Marcam", 7.2, False, liga, hora


def _format_match(jogo: dict[str, Any]) -> str:
    partida, aposta, confianca, value, liga, hora = analisar_jogo(jogo)
    value_tag = " · <b>VALUE</b>" if value else ""
    return (
        f"<b>{escape(partida)}</b>\n"
        f"<i>{escape(liga)} · {escape(hora)}</i>\n"
        f"Palpite: <b>{escape(aposta)}</b> · Confiança: "
        f"<b>{confianca:.1f}/10</b>{value_tag}\n"
    )


def _register_handlers(bot: TeleBot) -> None:
    @bot.message_handler(commands=["start"])
    def boas_vindas(message: Any) -> None:
        texto = (
            f"👋 <b>{BOT_NAME}</b>\n\n"
            "Agora com dados reais de jogos do dia.\n"
            "Digite /palpite para ver as análises de hoje.\n\n"
            "Use /ajuda para conhecer todos os comandos."
        )
        bot.send_message(message.chat.id, texto, parse_mode="HTML")

    @bot.message_handler(commands=["ajuda", "help"])
    def ajuda(message: Any) -> None:
        texto = (
            f"<b>{BOT_NAME}</b> — comandos\n\n"
            "/palpite — buscar jogos e gerar palpites de hoje\n"
            "/status — verificar se o bot está online\n"
            "/ajuda — mostrar esta mensagem\n\n"
            "<i>A análise é informativa, não garante resultados. "
            "Apenas maiores de 18 anos e sempre jogue com responsabilidade.</i>"
        )
        bot.send_message(message.chat.id, texto, parse_mode="HTML")

    @bot.message_handler(commands=["palpite", "jogos"])
    def mandar_palpites(message: Any) -> None:
        bot.send_message(
            message.chat.id,
            "⏳ Buscando jogos reais de futebol de hoje...",
        )
        try:
            jogos = buscar_jogos_hoje()
        except requests.RequestException:
            logger.exception("Falha ao consultar TheSportsDB")
            bot.send_message(
                message.chat.id,
                "Não consegui consultar os jogos agora. Tente novamente em alguns instantes.",
            )
            return
        except (ValueError, TypeError):
            logger.exception("Resposta inválida recebida do TheSportsDB")
            bot.send_message(
                message.chat.id,
                "A fonte de jogos retornou uma resposta inválida. Tente novamente mais tarde.",
            )
            return

        if not jogos:
            bot.send_message(
                message.chat.id,
                "Nenhum jogo de futebol encontrado para hoje na fonte consultada.",
            )
            return

        data = datetime.now().strftime("%d/%m/%Y")
        partes = [f"⚽ <b>PALPITES REAIS — {data}</b>\n"]
        partes.extend(_format_match(jogo) for jogo in jogos)
        partes.append(
            "⚠️ <i>Os palpites são uma análise automática e não garantem "
            "resultados. Apenas 18+. Jogue com responsabilidade.</i>"
        )
        bot.send_message(
            message.chat.id,
            "\n".join(partes),
            parse_mode="HTML",
        )

    @bot.message_handler(commands=["status"])
    def status(message: Any) -> None:
        bot.send_message(
            message.chat.id,
            f"✅ <b>{BOT_NAME}</b> está online.",
            parse_mode="HTML",
        )


def build_bot(token: str) -> TeleBot:
    bot = telebot.TeleBot(token)
    _register_handlers(bot)
    return bot


def main() -> None:
    token = os.getenv(TOKEN_ENV) or os.getenv(LEGACY_TOKEN_ENV)
    if not token:
        raise RuntimeError(
            f"Defina o segredo {TOKEN_ENV} antes de iniciar o bot."
        )

    bot = build_bot(token)
    logger.info("%s iniciando com TheSportsDB...", BOT_NAME)
    bot.infinity_polling(timeout=20, long_polling_timeout=20)


if __name__ == "__main__":
    main()