#!/usr/bin/env python3
import os, glob, tarfile, datetime, csv, requests, subprocess
import mysql.connector
from minio import Minio
from netmiko import ConnectHandler
from difflib import unified_diff

ENV_DB      = ".env_database"
ENV_MINIO   = ".env_minio"
ENV_TG      = ".env_telegram"
CSV_FILE    = "routers.csv"
LOG_DIR     = "device_logs"
CFG_DIR     = "configs"



def load_env(path):
    data = {}
    with open(path) as f:
        for line in f:
            if not line.strip() or line.startswith("#"): continue
            k,v = line.strip().split("=",1)
            data[k] = v
    return data

#load configs
db_env    = load_env(ENV_DB)
minio_env = load_env(ENV_MINIO)
tg_env    = load_env(ENV_TG)

#telegram setup
tg_url  = f"https://api.telegram.org/bot{tg_env['TELEGRAM_TOKEN']}/sendMessage"
CHAT_ID = tg_env["TELEGRAM_CHAT_ID"]

def send_telegram(text):
    requests.post(tg_url, json={"chat_id": CHAT_ID, "text": text})


#minio setup
minio_client = Minio(
    minio_env["MINIO_ENDPOINT"],
    access_key=minio_env["MINIO_ACCESS_KEY"],
    secret_key=minio_env["MINIO_SECRET_KEY"],
    secure=False
)
#debug of minio! Dont need it 
#print("env_minio keys:", list(minio_env.keys()))
bucket = minio_env["MINIO_ARCHIVE_BUCKET"]

#load device creds from CSV
creds_map = {}
with open(CSV_FILE, newline="") as f:
    for row in csv.DictReader(f):
        name = row["router_name"].strip()
        creds_map[name] = {
            "device_type": row["device_type"].strip(),
            "username":    row["username"].strip(),
            "password":    row["password"].strip(),
            "host_csv":    row["host"].strip(),
        }
#archiving the logs in daily format with dates and notify if it is done
def archive_logs():
    today = datetime.date.today().isoformat()
    archive_name = f"logs_{today}.tar.gz"
    archive_path = os.path.join("/tmp", archive_name)
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(LOG_DIR, arcname=os.path.basename(LOG_DIR))
    object_name = f"every_days_logs/{archive_name}"
    minio_client.fput_object(bucket, object_name, archive_path)
    send_telegram(f"archive_saved:{object_name}")
    os.remove(archive_path)

#checking configs if something changes!
def check_configs():
    os.makedirs(CFG_DIR, exist_ok=True)
    db = mysql.connector.connect(
        host=db_env["DB_HOST"],
        user=db_env["DB_USER"],
        password=db_env["DB_PASS"],
        database=db_env["DB_NAME"]
    )
    cur = db.cursor()
    cur.execute("SELECT id,router_name,ip FROM routers")
    for router_id, router_name, ip_db in cur.fetchall():
        info = creds_map.get(router_name)
        if not info:
            continue
        host     = info["host_csv"]
        dev_type = info["device_type"]
        user     = info["username"]
        pwd      = info["password"]
        try:
            conn = ConnectHandler(
                device_type=dev_type,
                host=host,
                username=user,
                password=pwd
            )
            conn.send_command("terminal length 0")
            current_cfg = conn.send_command("show running-config")
            conn.disconnect()
        except Exception:
            continue
        today = datetime.date.today().isoformat()
        new_fname = f"{today}_{router_name}${router_id}.cfg"
        new_path  = os.path.join(CFG_DIR, new_fname)
        pattern   = os.path.join(CFG_DIR, f"*_{router_name}${router_id}.cfg")
        prev_files = sorted(glob.glob(pattern))
        if not prev_files:
            with open(new_path, "w") as f:
                f.write(current_cfg)
            send_telegram(f"initial_config_saved:{new_fname}")
            continue
        prev_path = prev_files[-1]
        with open(prev_path) as f:
            prev_cfg = f.read()
        if current_cfg != prev_cfg:
            diff = "\n".join(unified_diff(
                prev_cfg.splitlines(),
                current_cfg.splitlines(),
                fromfile=prev_path,
                tofile=new_path,
                lineterm=""
            ))
            send_telegram(f"config_changed:{router_name}\ndiff:\n{diff}")
            with open(new_path, "w") as f:
                f.write(current_cfg)

    cur.close()
    db.close()

def main():
    archive_logs()
    check_configs()

if __name__ == "__main__":
    main()
