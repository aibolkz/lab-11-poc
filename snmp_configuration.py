#!/usr/bin/env python3
import csv
from netmiko import ConnectHandler

community = "lab11"
csv_file = "routers.csv"

def configure_snmp(device):
    conn = ConnectHandler(**device)
    conn.send_config_set([f"snmp-server community {community} RO"])  #setsnmpcommunity
    conn.send_command_timing("write memory")  #saveconfig
    conn.disconnect()  #disconnect

def main():
    with open(csv_file, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            device = {
                "device_type": row["device_type"],
                "host":        row["host"],
                "username":    row["username"],
                "password":    row["password"],
            }
            configure_snmp(device)
            print(f"{row['router_name']} configured")  #printresult

if __name__ == "__main__":
    main()
