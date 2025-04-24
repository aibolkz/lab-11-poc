#!/usr/bin/env python3
import os
import csv
import datetime
import subprocess
import mysql.connector
from minio import Minio
from minio.error import S3Error
from netmiko import ConnectHandler

ENV_DB    = ".env_database"
ENV_MINIO = ".env_minio"
CSV_FILE  = "routers.csv"
LOG_DIR   = "device_logs"

def load_env(path):
    d = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"): continue
            k,v = line.split("=",1)
            d[k] = v
    return d

# загружаем настройки
db_env    = load_env(ENV_DB)
minio_env = load_env(ENV_MINIO)

DB_CONFIG = {
    'host':     db_env['DB_HOST'],
    'user':     db_env['DB_USER'],
    'password': db_env['DB_PASS'],
    'database': db_env['DB_NAME'],
}

minio_client = Minio(
    minio_env['MINIO_ENDPOINT'],
    access_key=minio_env['MINIO_ACCESS_KEY'],
    secret_key=minio_env['MINIO_SECRET_KEY'],
    secure=False
)
bucket = minio_env['MINIO_BUCKET']

os.makedirs(LOG_DIR, exist_ok=True)

def main():
    # читаем креды из CSV по имени роутера
    creds = {}
    with open(CSV_FILE, newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            name = row["router_name"].strip()
            creds[name] = {
                "device_type": row["device_type"].strip(),
                "username":    row["username"].strip(),
                "password":    row["password"].strip(),
                "host_csv":    row["host"].strip(),  # на случай, если CSV и БД разнятся
            }

    db  = mysql.connector.connect(**DB_CONFIG)
    cur = db.cursor()
    # создаём таблицу логов загрузок, если нет
    cur.execute("""
    CREATE TABLE IF NOT EXISTS logs_upload (
      id INT AUTO_INCREMENT PRIMARY KEY,
      router_id INT,
      object_name VARCHAR(255),
      uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      success BOOLEAN
    )
    """)
    db.commit()

    # Берём из БД только id, router_name и ip
    cur.execute("SELECT id, router_name, ip FROM routers")
    for router_id, router_name, ip_db in cur.fetchall():
        info = creds.get(router_name)
        if not info:
            # нет записи в CSV — пропускаем
            continue

        host = info["host_csv"]  # или используем ip_db
        dev_type = info["device_type"]
        user     = info["username"]
        pwd      = info["password"]

        # достаём логи через SSH
        try:
            conn = ConnectHandler(
                device_type=dev_type,
                host=host,
                username=user,
                password=pwd
            )
            conn.send_command("terminal length 0")
            output = conn.send_command("show logging")
            conn.disconnect()
        except Exception as e:
            output = f"ERROR fetching logs: {e}"

        # сохраняем локально
        ts    = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        fname = f"{router_id}_{ts}.log"
        fpath = os.path.join(LOG_DIR, fname)
        with open(fpath, "w") as f:
            f.write(output)

        # загружаем в MinIO
        date_pref   = datetime.datetime.utcnow().strftime("%Y-%m-%d")
        object_name = f"{date_pref}/{fname}"
        try:
            minio_client.fput_object(bucket, object_name, fpath)
            success = True
        except S3Error:
            success = False

        # записываем результат в БД
        cur.execute(
            "INSERT INTO logs_upload (router_id,object_name,success) VALUES (%s,%s,%s)",
            (router_id, object_name, success)
        )
        db.commit()

    cur.close()
    db.close()

if __name__=="__main__":
    main()
