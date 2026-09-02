from threading import Thread

from bot.bot import main as run_bot
from bot.health_server import run_flask


if __name__ == "__main__":
    Thread(target=run_flask, daemon=True, name="health-server").start()
    run_bot()
