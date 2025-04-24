#!/usr/bin/env python3
import csv
import mysql.connector

ENV_FILE = ".env_database"
CSV_FILE = "routers.csv"

def load_env(path):
    data = {}
    with open(path) as f:
        for line in f:
            if not line.strip() or line.startswith("#"):
                continue
            key, val = line.strip().split("=", 1)
            data[key] = val
    return data


env = load_env(ENV_FILE)
DB_CONFIG = {
    'host':     env['DB_HOST'],
    'user':     env['DB_USER'],
    'password': env['DB_PASS'],
    'database': env['DB_NAME'],
}



#main
def main():
    conn = mysql.connector.connect(**DB_CONFIG)
    cur  = conn.cursor()
    # instead TRUNCATE use DELETE
    cur.execute("DELETE FROM routers")
    conn.commit()

    with open(CSV_FILE, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["router_name"].strip()
            ip   = row["host"].strip()
            cur.execute(
                "INSERT INTO routers (router_name, ip) VALUES (%s, %s)",
                (name, ip)
            )

    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
