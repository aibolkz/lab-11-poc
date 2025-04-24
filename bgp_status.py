#!/usr/bin/env python3
import csv, subprocess
from datetime import datetime

community="public"
routers_csv="routers.csv"
bgp_csv="bgp.csv"


def get_bgp_states(ip):
    cmd=["snmpwalk","-v2c","-c",community,ip,"1.3.6.1.2.1.15.3.1.2"]
    try:
        out=subprocess.check_output(cmd, text=True)
    except subprocess.CalledProcessError:
        return {}
    states={}
    for line in out.splitlines():
        if "INTEGER" in line:
            left,right=line.split("=",1)
            oid=left.strip()
            val=right.split("INTEGER:")[1].strip()
            peer=".".join(oid.split(".")[-4:])
            states[peer]=int(val)
    return states


def main():
    routers={}
    with open(routers_csv,newline="") as f:
        reader=csv.DictReader(f)
        for row in reader:
            routers[row["router_name"]]=row["host"]


    with open(bgp_csv,newline="") as f:
        reader=csv.DictReader(f)
        for row in reader:
            if row["bgp_peer"].lower()!="yes": continue
            hostname=row["hostname"].strip()
            router_ip=routers.get(hostname)
            if not router_ip: continue
            neighbors=[p.strip() for p in row["neighbors"].split(",")]
            print(f"{datetime.now()} checking {hostname} {router_ip}")
            states=get_bgp_states(router_ip)
            for peer in neighbors:
                code=states.get(peer)
                status="OK" if code==6 else f"down({code})"
                print(f"{hostname} BGP peer {peer} state is {status}")
            print()

if __name__=="__main__":
    main()
