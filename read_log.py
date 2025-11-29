
import os

log_file = "/Users/felixdevasia/projects/hackathons/google/FarmFlow/telegram_bot.log"
if os.path.exists(log_file):
    with open(log_file, "r") as f:
        lines = f.readlines()
        print("".join(lines[-200:]))
else:
    print("Log file not found")
