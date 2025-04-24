#!/usr/bin/env python3
import csv  
import subprocess 
import time 
import requests 

import os

def load_env(path):
    data = {}
    with open(path) as f:
        for line in f:
            if not line.strip() or line.startswith("#"): continue
            k, v = line.strip().split("=", 1)
            data[k] = v
    return data

#load telegram info
env_file = ".env_telegram"
env = load_env(env_file)

#set values to telegram functions
csv_file = env.get("CSV_FILE", "routers.csv")  # default routers.csv if not in .env
telegram_token = env["TELEGRAM_TOKEN"]
telegram_chat_id = env["TELEGRAM_CHAT_ID"]
tg_url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"

def ping(ip):
    return subprocess.call(
        ["ping","-c","1","-W","1",ip],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )==0  #returntrueifup

def send_telegram(text):
    requests.post(tg_url, json={"chat_id":telegram_chat_id, "text":text})  #sendmessage

def main():
    with open(csv_file, newline="") as f:
        reader=csv.DictReader(f)  
        for row in reader:
            name=row["router_name"].strip()  
            ip=row["host"].strip()  
            success=False  
            for _ in range(3):  
                if ping(ip):
                    success=True  
                    break
                time.sleep(5)  
            if not success:
                send_telegram(f"{name} {ip} is unreachable after 3 attempts")  #alert

if __name__=="__main__":
    main()  
