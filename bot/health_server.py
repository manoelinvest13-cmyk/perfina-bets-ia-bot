"""Minimal HTTP health endpoint for Render."""

from __future__ import annotations

import logging
import os

from flask import Flask


app = Flask(__name__)
logger = logging.getLogger("Perfina Bets IA health")


@app.get("/")
def home() -> str:
    return "Bot Perfina Bets Online!"


def run_flask() -> None:
    port = int(os.getenv("PORT", "10000"))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False,
    )