#!/usr/bin/env python3
import csv
from netmiko import ConnectHandler

community   = "public"
trap_host   = "198.51.100.2"    
routers_csv = "routers.csv"     



def configure_traps(device):
    conn = ConnectHandler(**device)
    cmds = [
        f"snmp-server host {trap_host} version 2c {community}",
        "snmp-server enable traps bgp",
        "snmp-server enable traps snmp linkdown"
    ]
    conn.send_config_set(cmds)
    conn.save_config()
    conn.disconnect()



def main():
    with open(routers_csv, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            device = {
                "device_type": row["device_type"],
                "host":        row["host"],
                "username":    row["username"],
                "password":    row["password"],
            }
            configure_traps(device)
            print(f"{row['router_name']} traps configured")



if __name__ == "__main__":
    main()
