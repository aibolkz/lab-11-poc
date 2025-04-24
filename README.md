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

### 2. Scripts and  Roles

**snmp_configuration.py**	Once	routers.csv	Sets snmp-server community lab11 RO on each device

**configure_traps.py**	Once	routers.csv	Enables snmp-server enable traps bgp peerDown and snmp-server enable traps snmp linkDown

**import_routers_db.py**	Once	routers.csv	Fills DB table routers(id, router_name, ip)

**ping_monitor.py**	Every 5 minutes (cron)	routers table	Pings devices, keeps state file, sends Telegram on down/up change

**bgp_status.py**	On demand or cron	routers.csv & routers table	SNMP-walk of BGP peerState → console output or later DB insert

**check_logs.py**	Hourly (cron)	routers table & routers.csv	SSH show logging → local files → upload to MinIO device-logs/ → record in DB

**daily_tasks.py**	Daily (cron)	routers table & routers.csv	1) Archive device_logs/ → MinIO /everyday-archives/ + Telegram notification
2) SSH show running-config diff with last → save new config + Telegram on change


### 3. Adding a New Device
Add a line in routers.csv with fields:
router_name,device_type,host,username,password

Run once:
```python3 import_routers_db.py```
All monitoring scripts will now pick up the new router from the routers table automatically.

### 4. Environment Variable File
Put a single .env file in the project root directory:

```# Database settings
DB_HOST=localhost
DB_USER=monitor
DB_PASS=password!
DB_NAME=monitoring

# MinIO settings
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=device-logs
MINIO_ARCHIVE_BUCKET=everyday-archives

# Telegram bot settings
TELEGRAM_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here ```

## All scripts use the same loader to read .env.

