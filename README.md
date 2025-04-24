# Documentation of PoC Monitoring for WDTC Lab-11

## 1. Logic and Overview

The system is divided into 2 phases: 

1. **Initial configuration** (execute once) 
 
   * Set up community for SNMP and traps
   * Grab routers from the CSV file and populate the Database
   * The above scripts do not run with every check

2. **Continuous Monitoring** (execute at intervals)

   * All mentioned scripts access devices from the `routers` table (`id, router_name, ip`) 

   * Execute actions such as:
   
       * Ping checks
       
       * BGP state SNMP query
       
       * log collection and archiving at MinIO
       
       * diff and archive show running-config
       
       * log configuration changes and send alerts via Telegram
        

### Logical flow

```

1) Initial Setup
 
   ├─ snmp_configuration.py    # set SNMP community on all routers
   ├─ configure_traps.py       # enable only-down traps
   └─ import_routers_db.py      # load routers.csv into DB table

2) Monitoring Loop
   ├─ ping_monitor.py         # ping + state file + Telegram alerts (every 5 min)
   ├─ bgp_status.py           # SNMP-walk BGP status → console or DB   
   ├─ check_logs.py           ## SSH show logging → MinIO + logs_upload table (hourly)
   └─ daily_tasks.py           ## archive logs → MinIO + config-diff → MinIO + Telegram (have to add into the cron)
```

