#!/usr/bin/env python3
import sys, requests
from datetime import datetime


env_file=".env_telegram"


def load_env(path):
    data={}
    with open(path) as f:
        for line in f:
            if not line.strip() or line.startswith("#"):continue
            k,v=line.strip().split("=",1)
            data[k]=v
    return data

env=load_env(env_file)

TOKEN=env["TELEGRAM_TOKEN"]
CHAT_ID=env["TELEGRAM_CHAT_ID"]

TOKEN   = "7739671202:AAHo32x11NjNvm0rtURGMhoYHwtUZrWg7qw"
CHAT_ID = "771415687"
URL     = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

def send(text):
    requests.post(URL, json={"chat_id": CHAT_ID, "text": text})

def main():
    raw = sys.stdin.read().strip()
    if not raw:
        return
    # you can parse raw here, but for now just forward it
    msg = f"[{datetime.now().isoformat()}] SNMP TRAP:\n{raw}"
    send(msg)

if __name__ == "__main__":
    main()

