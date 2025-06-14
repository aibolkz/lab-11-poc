#!/usr/bin/env python3
import csv  #
import subprocess  #
from datetime import datetime  #

csv_file = "routers.csv"  



def ping_host(ip):
    try:
        ret = subprocess.call(
            ["ping", "-c", "1", "-W", "1", ip],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        return ret == 0  #returntrueifup
    except:
        return False  
        


def main():
    with open(csv_file, newline="") as f:
        reader = csv.DictReader(f)  #readcsvfile
        for row in reader:
            name = row["router_name"].strip()
            ip = row["host"].strip()
            up = ping_host(ip)  #checkuptime
            status = "up" if up else "down"
            print(f"{datetime.now()} {name} {ip} is {status}")  #printstatus




if __name__ == "__main__":
    main()  
